from django.db import models
from django.core.exceptions import ValidationError
import uuid
import re


def validate_barcode(value):
    # https://en.wikipedia.org/wiki/Universal_Product_Code
    # UPC-A is 12 digits; SLLLLLRRRRRC
    #   where S is the number system digit, L the left half of the code, R the right, and C the check digit
    # in number systems 0-1, 6-9, the left half is manufacturer, the right is product
    # in number system 2, the left half is product code, the right is pricing.
    #   if the first R is a 0 they are weight values, otherwise they are a price.
    # UPC-E is 8 digits SDDDDDRC. S may only be 0 or 1. R may be 0-9
    #   R controls which D values map to product or manufacturer
    # We also support UUID codes, which are used as a last resort for items that do not have either of the above barcodes

    if re.match(r"^\d{12}$", value):
        digits = [int(d) for d in value]
        # UPC check digit validation:
        # 3x(sum of odd positions) + sum of even positions should be divisible by 10
        total = 3 * sum(digits[0:11:2]) + sum(digits[1:11:2])
        if total % 10 != 19 - digits[12]:
            raise ValidationError("UPC-A length but invalid check digit.")
    elif re.match(r"^\d{8}$", value):
        # assume this is a UPC-E code, which we don't validate
        return True
    elif len(uuid.UUID(str(value)).hex) == 36:
        # assume we have scanned one of our custom uuid codes, which we dont validate
        return True
    raise ValidationError(
        "Scanned barcode does not appear to match UPC-A (12 digit), UPC-E (8 digit), or our custom barcode."
    )


class BaseItem(models.Model):
    name = models.CharField(max_length=30)
    manufacturer = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    barcode = models.CharField(
        max_length=36,  # UUID length is 36, UPC-A is 12, UPC-E is 8
        validators=[validate_barcode],
        unique=True,
    )
    normalized_barcode = models.CharField(
        max_length=36,
        editable=False,  # Only set programmatically
        db_index=True,
    )  # For efficient lookups

    def clean(self):
        # Check for duplicate name + manufacturer, excluding self
        duplicate_name = BaseItem.objects.filter(
            name=self.name, manufacturer=self.manufacturer
        )
        if self.pk:  # If editing existing item
            duplicate_name = duplicate_name.exclude(pk=self.pk)
        if duplicate_name.exists():
            raise ValidationError(
                {
                    "name": f'An item named "{self.name}" from "{self.manufacturer}" already exists'
                }
            )

        # Check for duplicate normalized barcode
        if self.barcode.startswith("2") and len(self.barcode) == 12:
            # For Type 2 UPCs, check if any item exists with same first 6 digits
            duplicate_barcode = BaseItem.objects.filter(
                barcode__startswith="2", barcode__regex=f"^{self.barcode[:6]}\\d{{6}}$"
            )
            if self.pk:  # If editing existing item
                duplicate_barcode = duplicate_barcode.exclude(pk=self.pk)
            if duplicate_barcode.exists():
                raise ValidationError(
                    {
                        "barcode": f"An item with this product code ({self.barcode[:6]}) already exists"
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call clean()
        # Normalize Type 2 UPCs by zeroing out the price portion
        if self.barcode.startswith("2") and len(self.barcode) == 12:
            self.normalized_barcode = f"{self.barcode[:6]}00000{self.barcode[-1]}"
        else:
            self.normalized_barcode = self.barcode
        super().save(*args, **kwargs)

    class Meta:
        unique_together = (("name", "manufacturer"),)

    def __str__(self):
        return "{} ({})".format(self.name, self.manufacturer)

    def deactivate(self):
        self.active = False
        self.save()

    def activate(self):
        self.active = True
        self.save()


class Location(models.Model):
    name = models.CharField(max_length=30, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{}".format(self.name)


class Inventory(models.Model):
    base_item = models.ForeignKey(BaseItem, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{} @ {}".format(self.base_item, self.location)

    class Meta:
        unique_together = ("base_item", "location")

    def deactivate(self):
        self.active = False
        self.save()

    def activate(self):
        self.active = True
        self.save()
