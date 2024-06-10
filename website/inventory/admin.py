# inventory_app/inventory/admin.py

from django.contrib import admin
from .models import BaseItem, Location, Inventory

admin.site.register(BaseItem)
admin.site.register(Location)
admin.site.register(Inventory)

