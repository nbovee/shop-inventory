from django import template
from inventory.models import Inventory

register = template.Library()


@register.filter
def filter_by_id(items, item_id):
    """Get an inventory item by ID from a queryset."""
    try:
        return Inventory.objects.get(id=item_id)
    except Inventory.DoesNotExist:
        return None
