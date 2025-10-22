from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ("inventory_item",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "implicit_id", "date", "item_count")
    list_filter = ("date",)
    search_fields = ("order_number", "implicit_id")
    readonly_fields = ("order_number", "date")
    inlines = [OrderItemInline]

    @admin.display(description="Items")
    def item_count(self, obj):
        """Display the number of items in this order."""
        return obj.items.count()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "inventory_item", "quantity")
    list_filter = ("order__date",)
    search_fields = ("order__order_number", "inventory_item__product__name")
    raw_id_fields = ("order", "inventory_item")
