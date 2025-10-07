import pytest
from checkout.templatetags.checkout_filters import filter_by_barcode, filter_by_id
from inventory.models import Product, Location, Inventory

pytestmark = pytest.mark.django_db


def test_filter_by_barcode_found(inventory_item):
    """Test filter_by_barcode when item is found"""
    inventory_items = [inventory_item]
    result = filter_by_barcode(inventory_items, "123456789012")
    assert result == inventory_item


def test_filter_by_barcode_not_found(inventory_item):
    """Test filter_by_barcode when item is not found"""
    inventory_items = [inventory_item]
    result = filter_by_barcode(inventory_items, "999999999999")
    assert result is None


def test_filter_by_barcode_empty_list():
    """Test filter_by_barcode with empty list"""
    result = filter_by_barcode([], "123456789012")
    assert result is None


def test_filter_by_id_found(inventory_item):
    """Test filter_by_id when item is found"""
    result = filter_by_id([], inventory_item.id)
    assert result == inventory_item


def test_filter_by_id_not_found():
    """Test filter_by_id when item is not found"""
    result = filter_by_id([], 99999)
    assert result is None
