import pytest
from django.contrib.auth import get_user_model
from inventory.models import Product, Location, Inventory
from checkout.forms import AddToCartForm, ProcessOrderForm

pytestmark = pytest.mark.django_db


class MockRequest:
    """Mock request object for testing"""

    def __init__(self, user=None):
        self.user = user if user else None


def test_add_to_cart_form_invalid_product_id():
    """Test AddToCartForm with invalid product_id"""
    form = AddToCartForm(data={"product_id": "99999", "quantity": 1}, cart={})
    assert not form.is_valid()


def test_add_to_cart_form_exceeding_quantity(inventory_item):
    """Test AddToCartForm when quantity exceeds available stock"""
    form = AddToCartForm(
        data={"product_id": str(inventory_item.id), "quantity": 100},
        cart={},
    )
    assert not form.is_valid()


def test_add_to_cart_form_save(inventory_item):
    """Test AddToCartForm save method"""
    form = AddToCartForm(
        data={"product_id": str(inventory_item.id), "quantity": 2},
        cart={},
    )
    assert form.is_valid()
    cart = form.save()
    assert str(inventory_item.id) in cart
    assert cart[str(inventory_item.id)] == 2


def test_process_order_form_empty_cart():
    """Test ProcessOrderForm with empty cart"""
    request = MockRequest()
    form = ProcessOrderForm(
        data={"implicit_id": "test@test.com"},
        cart={},
        request=request,
    )
    assert not form.is_valid()


def test_process_order_form_invalid_implicit_id(inventory_item):
    """Test ProcessOrderForm with invalid implicit_id"""
    request = MockRequest()
    form = ProcessOrderForm(
        data={"implicit_id": ""},
        cart={str(inventory_item.id): 2},
        request=request,
    )
    assert not form.is_valid()


def test_add_to_cart_form_cumulative(inventory_item):
    """Test AddToCartForm adding items cumulatively"""
    cart = {str(inventory_item.id): 2}
    form = AddToCartForm(
        data={"product_id": str(inventory_item.id), "quantity": 3},
        cart=cart,
    )
    assert form.is_valid()
    updated_cart = form.save()
    assert updated_cart[str(inventory_item.id)] == 5
