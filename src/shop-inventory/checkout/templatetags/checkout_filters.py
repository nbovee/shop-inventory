from django import template
from inventory.models import InventoryEntry

register = template.Library()


@register.filter
def filter_by_id(items, item_id):
    """Get an inventory item by ID from a queryset."""
    try:
        return InventoryEntry.objects.get(id=item_id)
    except InventoryEntry.DoesNotExist:
        return None
