from django.contrib import admin
from .models import Product, Location, InventoryEntry, ProductUUID

# Register your models here.
admin.site.register((Product, Location, InventoryEntry, ProductUUID))
