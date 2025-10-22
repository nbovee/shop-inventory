from django.db import models
from django.core.exceptions import ValidationError
import re


def barcode_is_upc_a(value):
    # Check if the value consists of exactly 12 digits
    return bool(re.match(r"^\d{12}$", value))


def barcode_is_upc_e(value):
    return bool(re.match(r"^\d{8}$", value))


def barcode_is_uuid(value):
    return bool(re.match(r"^[0-9a-fA-F]{32}$", value))


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
        # assume this is a UPC-A code, which we don't validate beyond length.
        return True
    elif barcode_is_upc_e(value):
        # assume this is a UPC-E code, which we don't validate beyond length.
        return True
    elif barcode_is_uuid(value):
        # assume we have scanned one of our custom uuid codes, which we dont validate beyond length.
        return True
    raise ValidationError(
        "Scanned barcode does not appear to match UPC-A (12 digit), UPC-E (8 digit), or our custom barcode."
    )


def normalize_barcode(barcode):
    """
    Normalize barcode value:
    - For number system 2 barcodes (variable weight items), keep only the first 6 digits
    - Otherwise, return the original barcode
    """
    # Check if it's a UUID first
    # For UPC-A barcodes
    if barcode_is_upc_a(barcode) and barcode.startswith("2"):
        # For number system 2, we only keep the first 6 digits (system digit + 5 item digits)
        return barcode[:6]

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
    # New field for normalized barcode
    normalized_barcode = models.CharField(
        max_length=36,
        db_index=True,
        unique=True,
        editable=False,  # This field shouldn't be directly editable in forms/admin
    )

    class Meta:
        unique_together = (("name", "manufacturer"),)

    def __str__(self):
        return "{} ({})".format(self.name, self.manufacturer)

    def save(self, *args, **kwargs):
        # Set the normalized barcode before saving
        self.normalized_barcode = normalize_barcode(self.barcode)
        super().save(*args, **kwargs)

    def activate(self):
        """Reactivate this product."""
        self.active = True
        self.save()


class Location(models.Model):
    name = models.CharField(max_length=30, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{}".format(self.name)

    def activate(self):
        """Reactivate this location."""
        self.active = True
        self.save()


class Inventory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_product"
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return "{} @ {}".format(self.product, self.location)

    class Meta:
        unique_together = ("product", "location")

    def activate(self):
        """Reactivate this inventory item (currently not used, as Inventory doesn't have active field)."""
        # Note: Inventory model doesn't have an 'active' field
        # This method exists for API consistency but doesn't do anything
        pass
