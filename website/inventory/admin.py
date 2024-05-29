# inventory_app/inventory/admin.py
from django.contrib import admin
from .models import Item

admin.site.register(Item)

