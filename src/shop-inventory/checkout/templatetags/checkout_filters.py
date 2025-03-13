from django import template
from inventory.models import Inventory, normalize_barcode

register = template.Library()


@register.filter
def filter_by_barcode(inventory_items, barcode):
    """
    Filter inventory items by product ID, using normalized_barcode for lookup
    """
    for item in inventory_items:
        if item.product.normalized_barcode == normalize_barcode(barcode):
            return item
    return None


@register.filter
def filter_by_id(items, item_id):
    """Get an inventory item by ID from a queryset."""
    try:
        return Inventory.objects.get(id=item_id)
    except Inventory.DoesNotExist:
        return None
