import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from inventory.models import Product, Location, Inventory
from checkout.models import Order

pytestmark = pytest.mark.django_db


def test_checkout_index_with_filter(client, inventory_item):
    """Test checkout index with product filter"""
    response = client.get(reverse("checkout:index") + "?filter=Test")
    assert response.status_code == 200
    assert inventory_item in response.context["inventory_items"]


def test_process_order_form_validation_error(client, inventory_item):
    """Test process order with form validation errors"""
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.save()

    # Try to process with invalid implicit_id
    data = {"implicit_id": ""}
    response = client.post(reverse("checkout:process_order"), data)
    assert response.status_code == 302


def test_process_order_exception_handling(client, inventory_item):
    """Test process order exception handling"""
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.save()

    # Process with valid data
    data = {"implicit_id": "user@rowan.edu"}
    response = client.post(reverse("checkout:process_order"), data)
    assert response.status_code == 302


def test_remove_from_cart_get_request(client, inventory_item):
    """Test remove from cart with GET request"""
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.save()

    # GET request should just redirect
    response = client.get(reverse("checkout:remove_from_cart"))
    assert response.status_code == 302
