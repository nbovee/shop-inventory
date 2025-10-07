import pytest
from django.utils import timezone
from inventory.models import Product, Location, Inventory
from checkout.models import Order, OrderItem

pytestmark = pytest.mark.django_db


def test_order_str(inventory_item):
    """Test Order __str__ method"""
    order = Order.objects.create(
        order_number="ORD12345",
        implicit_id="test@test.com",
    )
    OrderItem.objects.create(
        order=order,
        inventory_item=inventory_item,
        quantity=2,
    )
    # Test __str__ includes order number
    assert "ORD12345" in str(order)


def test_order_items(inventory_item):
    """Test Order with multiple items"""
    order = Order.objects.create(
        order_number="ORD12345",
        implicit_id="test@test.com",
    )
    OrderItem.objects.create(
        order=order,
        inventory_item=inventory_item,
        quantity=2,
    )
    assert order.items.count() == 1
    assert order.items.first().quantity == 2


def test_orderitem_str(inventory_item):
    """Test OrderItem __str__ method"""
    order = Order.objects.create(
        order_number="ORD12345",
        implicit_id="test@test.com",
    )
    order_item = OrderItem.objects.create(
        order=order,
        inventory_item=inventory_item,
        quantity=2,
    )
    # Test __str__ contains relevant info
    result = str(order_item)
    assert "2" in result or "Test Item" in result
