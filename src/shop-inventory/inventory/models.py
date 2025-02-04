from django.db import models
from django.core.exceptions import ValidationError
import uuid
import re


def validate_upc(value):
    # UPC-A is 12 digits
    # UPC-E is 8 digits
    if not re.match(r"^(\d{12}|\d{8})$", value):
        if not is_valid_uuid(value):
            raise ValidationError(
                "Value must be either a valid UUID, UPC-A (12 digits), or UPC-E (8 digits)"
            )


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


# Create your models here.


class BaseItem(models.Model):
    def generate_uuid():
        return str(uuid.uuid4())

    name = models.CharField(max_length=30)
    manufacturer = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    barcode = models.CharField(
        max_length=36,  # UUID length is 36, UPC-A is 12, UPC-E is 8
        validators=[validate_upc],
        unique=True,
        default=generate_uuid,  # Use a named function instead of lambda
    )

    class Meta:
        unique_together = ("name", "manufacturer")

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
