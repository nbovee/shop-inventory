from django.db import models

# Create your models here.


class BaseItem(models.Model):
    name = models.CharField(max_length=30)
    barcode_number = models.TextField(blank=True, default='')
    active = models.BooleanField(default=True)


class Location(models.Model):
    name = models.CharField(max_length=30)
    barcode_number = models.TextField()
    active = models.BooleanField(default=True)


class Inventory(models.Model):
    base_item = models.ForeignKey(BaseItem, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("base_item", "location")
