from django.contrib import admin
from .models import Product, Location, Inventory, ProductUUID

# Register your models here.
admin.site.register((Product, Location, Inventory, ProductUUID))
