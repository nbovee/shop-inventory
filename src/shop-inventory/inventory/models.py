from django.db import models
from django.core.exceptions import ValidationError
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

    if barcode_is_upc_a(value):
        digits = [int(d) for d in value]
        # UPC check digit validation:
        # 3x(sum of odd positions) + sum of even positions should be divisible by 10
        total = 3 * sum(digits[0:11:2]) + sum(digits[1:11:2])
        if total % 10 == 0 and digits[12] == 0:
            return True
        elif total % 10 == 10 - digits[12]:
            return True
        else:
            raise ValidationError("UPC-A length but invalid check digit.")
    elif barcode_is_upc_e(value):
        # assume this is a UPC-E code, which we don't validate
        return True
    elif barcode_is_uuid(value):
        # assume we have scanned one of our custom uuid codes, which we dont validate
        return True
    raise ValidationError(
        "Scanned barcode does not appear to match UPC-A (12 digit), UPC-E (8 digit), or our custom barcode."
    )


def barcode_is_upc_a(value):
    return re.match(r"^\d{12}$", value)


def barcode_is_upc_e(value):
    return re.match(r"^\d{8}$", value)


def barcode_is_uuid(value):
    return True if len(str(value)) == 32 else False


def normalize_barcode(barcode):
    """Normalize Type 2 UPCs by zeroing out the price portion
    Return all others untouched"""
    if len(barcode) == 12 and barcode[0] == "2":
        barcode = f"{barcode[:6]}00000{barcode[-1]}"
    return barcode


class Product(models.Model):
    name = models.CharField(max_length=30)
    manufacturer = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    barcode = models.CharField(
        max_length=32,  # UUID length is 32, UPC-A is 12, UPC-E is 8
        validators=[validate_barcode],
        unique=True,
    )
    normalized_barcode = models.CharField(
        max_length=32,
        editable=False,  # Only set programmatically
        db_index=True,
    )  # For efficient lookups

    def clean(self):
        # Check for duplicate name + manufacturer, excluding self
        duplicate_name = Product.objects.filter(
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
        test_barcode = normalize_barcode(self.barcode)
        if self.barcode.startswith("2") and len(self.barcode) == 12:
            # For Type 2 UPCs, check if any item exists with same first 6 digits
            duplicate_barcode = Product.objects.filter(normalize_barcode=test_barcode)
            if self.pk:  # If editing existing item
                duplicate_barcode = duplicate_barcode.exclude(pk=self.pk)
            if duplicate_barcode.exists():
                raise ValidationError(
                    {
                        "barcode": f"An item with this product code ({self.barcode[:6]}) already exists"
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        self.normalized_barcode = normalize_barcode(self.barcode)
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
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_product"
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{} @ {}".format(self.product, self.location)

    class Meta:
        unique_together = ("product", "location")

    def deactivate(self):
        self.active = False
        self.save()

    def activate(self):
        self.active = True
        self.save()


class ProductUUID(models.Model):
    base_item = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="uuid_barcodes"
    )
    uuid_barcode = models.CharField(
        max_length=36,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def active(self):
        return self.base_item.active

    def __str__(self):
        return f"{self.uuid_barcode} -> {self.base_item}"

    def deactivate(self):
        self.base_item.active = False
        self.base_item.save()
        self.save()

    def activate(self):
        self.base_item.active = True
        self.base_item.save()
        self.save()
