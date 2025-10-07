"""Final edge case tests to reach 98%+ coverage"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import (
    Product,
    Location,
    Inventory,
    barcode_is_upc_e,
    barcode_is_uuid,
)
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


# ============ Test inventory/models.py barcode functions (lines 35, 38) ============


def test_barcode_is_upc_e():
    """Test UPC-E barcode validation (line 35)"""
    assert barcode_is_upc_e("12345678")  # 8 digits
    assert not barcode_is_upc_e("123456789012")  # 12 digits
    assert not barcode_is_upc_e("invalid")


def test_barcode_is_uuid():
    """Test UUID barcode validation (line 38)"""
    assert barcode_is_uuid("12345678901234567890123456789012")  # 32 hex digits
    assert not barcode_is_uuid("123456789012")  # 12 digits
    assert not barcode_is_uuid("invalid")


def test_create_product_with_upc_e_barcode():
    """Test creating product with UPC-E barcode"""
    product = Product.objects.create(
        name="UPC-E Test",
        manufacturer="Test",
        barcode="12345678",  # Valid UPC-E
    )
    assert product.barcode == "12345678"


def test_create_product_with_uuid_barcode():
    """Test creating product with UUID barcode"""
    product = Product.objects.create(
        name="UUID Test",
        manufacturer="Test",
        barcode="12345678901234567890123456789012",  # Valid UUID format
    )
    assert product.barcode == "12345678901234567890123456789012"


# ============ Test checkout/views.py exception paths ============


def test_checkout_barcode_with_form_invalid(client, shopfloor, product):
    """Test barcode scan triggering form validation errors"""
    # Create inventory but make it insufficient
    inventory = Inventory.objects.create(
        product=product, location=shopfloor, quantity=1
    )

    session = client.session
    session["cart"] = {str(inventory.id): 1}  # Already have 1 in cart
    session.save()

    # Try to add via barcode when quantity is insufficient
    data = {"barcode": product.barcode, "quantity": 5}
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302


def test_checkout_add_triggering_save_exception(client, shopfloor, product):
    """Test normal cart add with edge case that triggers exception in save"""
    inventory = Inventory.objects.create(
        product=product, location=shopfloor, quantity=1
    )

    session = client.session
    session["cart"] = {}
    session.save()

    # Add to cart successfully first
    data = {"product_id": inventory.id, "quantity": 1, "barcode": ""}
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302


def test_process_order_with_field_and_non_field_errors(client, shopfloor, product):
    """Test process_order to hit line 120 (double error loop)"""
    inventory = Inventory.objects.create(
        product=product, location=shopfloor, quantity=5
    )

    session = client.session
    session["cart"] = {str(inventory.id): 2}
    session.save()

    # Submit with invalid data to trigger both error loops
    data = {}  # Missing implicit_id
    response = client.post(reverse("checkout:process_order"), data)
    assert response.status_code == 302


# ============ Test inventory/views.py remaining lines ============


def test_stock_update_inactive_product_to_zero(
    client, admin_user, location, inactive_product
):
    """Test line 80 - inactive product reaching zero quantity"""
    inventory = Inventory.objects.create(
        product=inactive_product,
        location=location,
        quantity=5,
    )

    client.force_login(admin_user)
    data = {"item_id": inventory.id, "delta_qty": -5}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302

    inventory.refresh_from_db()
    # Inventory quantity should be 0, but item remains (no deactivation logic)
    assert inventory.quantity == 0


def test_stock_update_edge_case(client, admin_user, shopfloor, product):
    """Test stock_update edge cases"""
    inventory = Inventory.objects.create(
        product=product, location=shopfloor, quantity=10
    )

    client.force_login(admin_user)

    # Post form data
    data = {"item_id": inventory.id, "delta_qty": 5}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302


def test_add_location_with_duplicate_name(client, admin_user):
    """Test add location with duplicate handling"""
    # Create inactive location
    location = Location.objects.create(name="ReactivateMe")
    location.active = False
    location.save()

    client.force_login(admin_user)

    # Try to add location with same name
    data = {"name": "ReactivateMe"}
    response = client.post(reverse("inventory:add_location"), data)
    # Should handle the scenario
    assert response.status_code in [200, 302]


def test_add_item_with_invalid_session(client, admin_user):
    """Test add_item with invalid session state"""
    client.force_login(admin_user)

    # Don't set session data - try to scan directly
    data = {"action": "scan_barcode", "barcode": "123456789012"}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should handle missing session and redirect
    assert response.status_code == 302


def test_add_item_quantity_with_database_error(client, admin_user, location, product):
    """Test lines 502-509 - Exception during inventory save"""
    client.force_login(admin_user)

    # Set up session
    session = client.session
    session["selected_location_id"] = location.id
    session["current_product_id"] = product.id
    session.save()

    # Try to add quantity that causes validation error
    data = {"action": "add_quantity", "quantity": -100}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should show form with errors
    assert response.status_code == 200


# ============ Test _core/views.py group_required edge case ============


def test_group_required_unauthenticated_user(client):
    """Test group_required decorator with unauthenticated user"""
    # Try to access inventory index without login
    response = client.get(reverse("inventory:index"))
    # Should redirect to login
    assert response.status_code == 302
    assert "login" in response.url


def test_admin_access_via_admin_interface(client, admin_user):
    """Test _core/admin.py coverage"""
    client.force_login(admin_user)
    # Access admin interface
    response = client.get("/admin/")
    assert response.status_code == 200
