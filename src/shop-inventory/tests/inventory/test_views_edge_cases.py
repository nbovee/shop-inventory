import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, Location, Inventory

pytestmark = pytest.mark.django_db


def test_add_item_location_missing_session_for_scan(client, admin_user):
    """Test scanning barcode without location in session"""
    client.force_login(admin_user)
    data = {
        "action": "scan_barcode",
        "barcode": "123456789012",
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should redirect with error
    assert response.status_code == 302


def test_add_item_with_new_barcode(client, admin_user, location):
    """Test scanning new barcode that doesn't exist"""
    client.force_login(admin_user)

    # Set location in session
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    # Scan a new barcode
    data = {
        "action": "scan_barcode",
        "barcode": "333333333333",
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should show form for creating new product or error
    assert response.status_code == 200


def test_edit_product_get_clears_session(client, admin_user):
    """Test that GET request clears edit_product_id from session"""
    client.force_login(admin_user)

    # Set product in session
    session = client.session
    session["edit_product_id"] = 999
    session.save()

    # GET request should clear it
    response = client.get(reverse("inventory:edit_product"))
    assert response.status_code == 200
    assert "edit_product_id" not in client.session


def test_stock_check_with_multiple_items(client, admin_user, location):
    """Test stock check displays multiple items correctly"""
    product1 = Product.objects.create(
        name="Item A",
        manufacturer="Manufacturer",
        barcode="111111111111",
    )
    product2 = Product.objects.create(
        name="Item B",
        manufacturer="Manufacturer",
        barcode="222222222222",
    )

    Inventory.objects.create(product=product1, location=location, quantity=5)
    Inventory.objects.create(product=product2, location=location, quantity=10)

    client.force_login(admin_user)
    response = client.get(reverse("inventory:stock_check"))
    assert response.status_code == 200
    assert location in response.context["items_in_location"]


def test_add_item_invalid_location_selection(client, admin_user):
    """Test selecting invalid location"""
    client.force_login(admin_user)
    data = {
        "action": "select_location",
        "location_id": 99999,  # Invalid location ID
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should redirect or show error (404)
    assert response.status_code in [302, 404]
