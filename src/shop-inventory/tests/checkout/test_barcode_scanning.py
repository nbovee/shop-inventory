import pytest
from django.urls import reverse
from inventory.models import Product, Location, Inventory

pytestmark = pytest.mark.django_db


def test_barcode_scan_success(client, inventory_item):
    """Test successful barcode scanning"""
    session = client.session
    session["cart"] = {}
    session.save()

    data = {
        "barcode": "123456789012",
        "quantity": 1,
    }
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302

    # Check cart was updated
    cart = client.session.get("cart", {})
    assert str(inventory_item.id) in cart


def test_barcode_scan_not_found(client, shopfloor):
    """Test barcode scanning with non-existent barcode"""
    session = client.session
    session["cart"] = {}
    session.save()

    data = {
        "barcode": "999999999999",
        "quantity": 1,
    }
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302

    # Check cart is empty
    cart = client.session.get("cart", {})
    assert not cart


def test_barcode_scan_invalid_form(client, inventory_item):
    """Test barcode scanning with invalid form data"""
    session = client.session
    session["cart"] = {}
    session.save()

    # Try to add more than available quantity
    data = {
        "barcode": "123456789012",
        "quantity": 999,
    }
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302


def test_barcode_scan_exception_handling(client, inventory_item):
    """Test barcode scanning exception handling"""
    # Don't initialize session to trigger exception path
    data = {
        "barcode": "123456789012",
        "quantity": 1,
    }
    response = client.post(reverse("checkout:index"), data)
    # Should redirect even with error
    assert response.status_code == 302


def test_remove_from_cart(client, inventory_item):
    """Test removing item from cart"""
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.save()

    data = {"product_id": str(inventory_item.id)}
    response = client.post(reverse("checkout:remove_from_cart"), data)
    assert response.status_code == 302

    # Check item was removed
    cart = client.session.get("cart", {})
    assert str(inventory_item.id) not in cart


def test_remove_from_cart_not_found(client):
    """Test removing non-existent item from cart"""
    session = client.session
    session["cart"] = {}
    session.save()

    data = {"product_id": "99999"}
    response = client.post(reverse("checkout:remove_from_cart"), data)
    assert response.status_code == 302


def test_remove_from_cart_no_product_id(client):
    """Test remove from cart without product_id"""
    response = client.post(reverse("checkout:remove_from_cart"), {})
    assert response.status_code == 302


def test_process_order_error_handling(client, inventory_item):
    """Test process order with invalid data"""
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.save()

    # Submit with invalid implicit_id
    data = {"implicit_id": ""}
    response = client.post(reverse("checkout:process_order"), data)
    assert response.status_code == 302

    # Cart should still exist since order failed
    assert "cart" in client.session
