import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, Location, Inventory

pytestmark = pytest.mark.django_db


def test_reactivate_product_get(client, admin_user, inactive_product):
    """Test reactivate product GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:reactivate_product"))
    assert response.status_code == 200
    assert "form" in response.context


def test_reactivate_product_post(client, admin_user, inactive_product):
    """Test reactivating a product"""
    client.force_login(admin_user)
    data = {"product": inactive_product.id}
    response = client.post(reverse("inventory:reactivate_product"), data)
    assert response.status_code == 302

    inactive_product.refresh_from_db()
    assert inactive_product.active


def test_reactivate_location_get(client, admin_user, inactive_location):
    """Test reactivate location GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:reactivate_location"))
    assert response.status_code == 200
    assert "form" in response.context


def test_reactivate_location_post(client, admin_user, inactive_location):
    """Test reactivating a location"""
    client.force_login(admin_user)
    data = {"location": inactive_location.id}
    response = client.post(reverse("inventory:reactivate_location"), data)
    assert response.status_code == 302

    inactive_location.refresh_from_db()
    assert inactive_location.active


def test_edit_product_get(client, admin_user, product):
    """Test edit product GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:edit_product"))
    assert response.status_code == 200
    assert "form" in response.context


def test_edit_product_select(client, admin_user, product):
    """Test edit product selection step"""
    client.force_login(admin_user)
    data = {
        "action": "select_product",
        "product": product.id,
    }
    response = client.post(reverse("inventory:edit_product"), data)
    assert response.status_code == 200
    assert "edit_product_id" in client.session


def test_edit_product_edit(client, admin_user, product):
    """Test editing a product"""
    client.force_login(admin_user)

    # First select the product
    session = client.session
    session["edit_product_id"] = product.id
    session.save()

    data = {
        "action": "edit_product",
        "name": "Updated Name",
        "manufacturer": "Updated Manufacturer",
        "barcode": product.barcode,
    }
    response = client.post(reverse("inventory:edit_product"), data)
    assert response.status_code == 302

    product.refresh_from_db()
    assert product.name == "Updated Name"


def test_edit_product_cancel(client, admin_user, product):
    """Test cancelling product edit"""
    client.force_login(admin_user)

    # First select the product
    session = client.session
    session["edit_product_id"] = product.id
    session.save()

    data = {"action": "cancel"}
    response = client.post(reverse("inventory:edit_product"), data)
    assert response.status_code == 302
    assert "edit_product_id" not in client.session


def test_edit_product_no_selection(client, admin_user):
    """Test editing without product selection"""
    client.force_login(admin_user)
    data = {
        "action": "edit_product",
        "name": "Test",
        "manufacturer": "Test",
    }
    response = client.post(reverse("inventory:edit_product"), data)
    # Should redirect with error message
    assert response.status_code == 302


def test_add_item_to_location_get(client, admin_user, location):
    """Test add item to location GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:add_item_to_location"))
    assert response.status_code == 200


def test_add_item_to_location_select(client, admin_user, location):
    """Test selecting location in add item workflow"""
    client.force_login(admin_user)
    data = {
        "action": "select_location",
        "location_id": location.id,
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 200
    assert "selected_location_id" in client.session


def test_add_item_to_location_scan(client, admin_user, location, product):
    """Test scanning barcode in add item workflow"""
    client.force_login(admin_user)

    # Set location in session
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    data = {
        "action": "scan_barcode",
        "barcode": product.barcode,
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 200
    assert "current_product_id" in client.session


def test_add_item_to_location_new_barcode(client, admin_user, location):
    """Test scanning new (non-existent) barcode"""
    client.force_login(admin_user)

    # Set location in session
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    data = {
        "action": "scan_barcode",
        "barcode": "111111111111",  # Non-existent barcode
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 200


def test_add_item_to_location_add_quantity(client, admin_user, location, product):
    """Test adding quantity in add item workflow"""
    client.force_login(admin_user)

    # Set location and product in session
    session = client.session
    session["selected_location_id"] = location.id
    session["current_product_id"] = product.id
    session.save()

    data = {
        "action": "add_quantity",
        "quantity": 5,
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 200

    # Check that inventory was created/updated
    assert Inventory.objects.filter(product=product, location=location).exists()


def test_add_item_to_location_cancel(client, admin_user, location):
    """Test cancelling add item workflow"""
    client.force_login(admin_user)

    # Set some session data
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    data = {"action": "cancel"}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 302
    assert "selected_location_id" not in client.session


def test_add_item_missing_session_data(client, admin_user):
    """Test add quantity without session data"""
    client.force_login(admin_user)
    data = {
        "action": "add_quantity",
        "quantity": 5,
    }
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should redirect with error
    assert response.status_code == 302


def test_remove_product_get(client, admin_user, product):
    """Test remove product GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:remove_product"))
    assert response.status_code == 200
    assert "form" in response.context
    assert "products" in response.context


def test_remove_location_get(client, admin_user, location):
    """Test remove location GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:remove_location"))
    assert response.status_code == 200
    assert "form" in response.context


def test_add_location_get(client, admin_user):
    """Test add location GET request"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:add_location"))
    assert response.status_code == 200
    assert "form" in response.context


def test_add_product_get_with_inactive_items(client, admin_user, inactive_product):
    """Test add product GET request shows inactive items"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:add_product"))
    assert response.status_code == 200
    assert "inactive_items" in response.context
    assert inactive_product in response.context["inactive_items"]
