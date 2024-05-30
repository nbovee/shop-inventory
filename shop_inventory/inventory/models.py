from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.


class base_item(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    barcode_number = models.TextField()
    active = models.BooleanField(default=True)


class location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    active = models.BooleanField(default=True)


class inventory(models.Model):
    id = models.IntegerField(primary_key=True)
    item_name = models.ForeignKey(base_item, on_delete=models.CASCADE)
    quantity = models.IntegerField(MinValueValidator(0, "Quantity must be >= 0"))
    barcode_number = models.TextField()
    location = models.ForeignKey(location, on_delete=models.CASCADE)
    notes = models.TextField()
