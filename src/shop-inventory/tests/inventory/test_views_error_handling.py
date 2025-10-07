import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, Location, Inventory

pytestmark = pytest.mark.django_db


def test_stock_update_with_exception(client, admin_user, location):
    """Test stock update with exception handling"""
    client.force_login(admin_user)
    # Create an inventory item with inactive product
    inactive_product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="111111111111",
    )
    inactive_product.active = False
    inactive_product.save()

    inventory_item = Inventory.objects.create(
        product=inactive_product,
        location=location,
        quantity=5,
    )

    # Try to reduce quantity to zero
    data = {"item_id": inventory_item.id, "delta_qty": -5}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302

    inventory_item.refresh_from_db()
    assert inventory_item.quantity == 0


def test_add_location_inactive_exists(client, admin_user):
    """Test add location with existing inactive location"""
    # Create inactive location
    location = Location.objects.create(name="InactiveTest")
    location.active = False
    location.save()

    client.force_login(admin_user)
    data = {"name": "InactiveTest"}
    response = client.post(reverse("inventory:add_location"), data)
    # Should either redirect (success) or show form (200)
    assert response.status_code in [200, 302]


def test_add_product_with_existing_inactive(client, admin_user):
    """Test add product with existing inactive product"""
    # Create inactive product
    product = Product.objects.create(
        name="Inactive",
        manufacturer="Test",
        barcode="222222222222",
    )
    product.active = False
    product.save()

    client.force_login(admin_user)
    data = {
        "name": "Inactive",
        "manufacturer": "Test",
        "barcode": "222222222222",
        "location": Location.objects.first().id,
        "quantity": 5,
    }
    response = client.post(reverse("inventory:add_product"), data)
    # Form should handle error or reactivation
    # Response might be 200 (form with errors) or 302 (redirect)
    assert response.status_code in [200, 302]


def test_add_item_invalid_quantity(client, admin_user, location, product):
    """Test add item with invalid quantity"""
    client.force_login(admin_user)

    # Set location and product in session
    session = client.session
    session["selected_location_id"] = location.id
    session["current_product_id"] = product.id
    session.save()

    data = {
        "action": "add_quantity",
        "quantity": -5,  # Invalid negative quantity
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should show form with errors
    assert response.status_code == 200


def test_add_item_exception_handling(client, admin_user, location, product):
    """Test add item with exception during save"""
    client.force_login(admin_user)

    # Set location and product in session
    session = client.session
    session["selected_location_id"] = location.id
    session["current_product_id"] = product.id
    session.save()

    # Create existing inventory to test update path
    Inventory.objects.create(
        product=product,
        location=location,
        quantity=5,
    )

    data = {
        "action": "add_quantity",
        "quantity": 10,
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should succeed and update existing inventory
    assert response.status_code == 200

    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 15


def test_edit_product_invalid_form(client, admin_user, product):
    """Test edit product with invalid form data"""
    client.force_login(admin_user)

    # Set product in session
    session = client.session
    session["edit_product_id"] = product.id
    session.save()

    data = {
        "action": "edit_product",
        "name": "",  # Invalid empty name
        "manufacturer": "Test",
        "barcode": product.barcode,
    }
    response = client.post(reverse("inventory:edit_product"), data)
    # Should show form with errors
    assert response.status_code == 200
    assert "edit_product_id" in client.session


def test_add_item_scan_invalid_barcode(client, admin_user, location):
    """Test scanning invalid barcode"""
    client.force_login(admin_user)

    # Set location in session
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    data = {
        "action": "scan_barcode",
        "barcode": "invalid",  # Invalid barcode format
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should show form with error
    assert response.status_code == 200


def test_manage_inventory_view(client, admin_user):
    """Test manage inventory view"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:manage_inventory"))
    assert response.status_code == 200
