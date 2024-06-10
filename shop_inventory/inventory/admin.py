from django.contrib import admin
from .models import BaseItem, Location, Inventory

# Register your models here.
admin.site.register((BaseItem, Location, Inventory))
