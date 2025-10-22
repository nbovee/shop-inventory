from django.contrib import admin
from .models import Product, Location, Inventory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "manufacturer", "barcode", "normalized_barcode", "active")
    list_filter = ("active",)
    search_fields = ("name", "manufacturer", "barcode", "normalized_barcode")
    readonly_fields = ("normalized_barcode",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity")
    list_filter = ("location", "product__active")
    search_fields = ("product__name", "product__manufacturer", "location__name")
    raw_id_fields = ("product", "location")
