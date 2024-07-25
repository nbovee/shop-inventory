from django.db import models
import uuid
# Create your models here.


class BaseItem(models.Model):
    name = models.CharField(max_length=30, unique=True)
    variant = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    def __str__(self):
        return "{} ({})".format(self.name, self.variant)

class Location(models.Model):
    name = models.CharField(max_length=30, unique=True)
    active = models.BooleanField(default=True)


class Inventory(models.Model):
    base_item = models.ForeignKey(BaseItem, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    uuid = models.UUIDField(default = uuid.uuid4, editable = True, unique=True)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("base_item", "location")
