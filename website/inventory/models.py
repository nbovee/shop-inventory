# inventory_app/inventory/models.py
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    barcode = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name
