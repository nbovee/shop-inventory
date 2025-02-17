import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, Location, Inventory
from unittest.mock import patch

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def admin_user():
    User = get_user_model()
    user = User.objects.create_superuser(
        username="admin",
        password="adminpass123",
    )
    # Add necessary permissions
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def product():
    return Product.objects.create(
        name="Test Item",
        manufacturer="Test Manufacturer",
    )


@pytest.fixture
def location():
    return Location.objects.create(
        name="Test Location",
    )


@pytest.fixture
def inventory_item(product, location):
    return Inventory.objects.create(
        product=product,
        location=location,
        quantity=10,
    )


def test_index_view(client, user, inventory_item):
    """Test the inventory index view"""
    client.force_login(user)
    response = client.get(reverse("inventory:index"))
    assert response.status_code == 200
    assert inventory_item in response.context["inventory_items"]


def test_index_view_with_search(client, user, inventory_item):
    """Test the inventory index view with search"""
    client.force_login(user)
    response = client.get(reverse("inventory:index") + "?search=Test")
    assert response.status_code == 200
    assert inventory_item in response.context["inventory_items"]


def test_stock_check_view(client, user, inventory_item):
    """Test the stock check view"""
    client.force_login(user)
    response = client.get(reverse("inventory:stock_check"))
    assert response.status_code == 200
    items_in_location = response.context["items_in_location"]
    assert inventory_item.location in items_in_location
    assert inventory_item in items_in_location[inventory_item.location]


def test_stock_update_view(client, user, inventory_item):
    """Test updating stock quantity"""
    client.force_login(user)
    initial_quantity = inventory_item.quantity
    data = {"item_id": inventory_item.id, "delta_qty": 5}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302
    inventory_item.refresh_from_db()
    assert inventory_item.quantity == initial_quantity + 5


def test_stock_update_view_negative(client, user, inventory_item):
    """Test updating stock quantity with negative value"""
    client.force_login(user)
    initial_quantity = inventory_item.quantity
    data = {"item_id": inventory_item.id, "delta_qty": -inventory_item.quantity - 1}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302
    inventory_item.refresh_from_db()
    assert inventory_item.quantity == initial_quantity  # Quantity shouldn't change


def test_add_inventory_view(client, admin_user, product, location):
    """Test adding new inventory"""
    client.force_login(admin_user)
    data = {
        "product": product.id,
        "location": location.id,
        "quantity": 5,
        "barcode": "123456789012",  # Adding required barcode field
    }
    response = client.post(reverse("inventory:add_inventory"), data)
    assert response.status_code == 302  # Should redirect after successful addition
    assert Inventory.objects.filter(product=product, location=location).exists()


def test_add_product_view(client, admin_user):
    """Test adding a new product"""
    client.force_login(admin_user)
    data = {"name": "New Item", "manufacturer": "New Manufacturer"}
    response = client.post(reverse("inventory:add_product"), data)
    assert response.status_code == 302
    assert Product.objects.filter(name="New Item").exists()


def test_remove_product_view(client, admin_user, product, inventory_item):
    """Test removing a product"""
    client.force_login(admin_user)
    data = {"product": product.id}
    response = client.post(reverse("inventory:remove_product"), data)
    assert response.status_code == 302
    product.refresh_from_db()
    assert not product.active


def test_add_location_view(client, admin_user):
    """Test adding a new location"""
    client.force_login(admin_user)
    data = {"name": "New Location"}
    response = client.post(reverse("inventory:add_location"), data)
    assert response.status_code == 302
    assert Location.objects.filter(name="New Location").exists()


def test_add_location_view_duplicate(client, admin_user, location):
    """Test adding a duplicate location"""
    client.force_login(admin_user)
    data = {"name": location.name}
    response = client.post(reverse("inventory:add_location"), data)
    assert response.status_code == 200  # Returns form with errors
    assert "already exists" in str(response.content)


def test_remove_location_view(client, admin_user, location):
    """Test removing a location"""
    client.force_login(admin_user)
    data = {"location": location.id}
    response = client.post(reverse("inventory:remove_location"), data)
    assert response.status_code == 302
    location.refresh_from_db()
    assert not location.active


def test_remove_location_with_inventory(client, admin_user, inventory_item):
    """Test removing a location that has inventory items"""
    client.force_login(admin_user)
    data = {"location": inventory_item.location.id}
    response = client.post(reverse("inventory:remove_location"), data)
    assert response.status_code == 302
    inventory_item.location.refresh_from_db()
    assert inventory_item.location.active  # Location should still be active


def test_qrcode_sheet_view(client, admin_user):
    """Test generating QR code sheet"""
    client.force_login(admin_user)
    with patch("inventory.views.barcode_page_generation") as mock_gen:
        mock_gen.return_value = b"%PDF-1.4\n%EOF\n"
        response = client.get(reverse("inventory:barcodes"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        mock_gen.assert_called_once_with()


def test_stock_update_view_invalid_item(client, user):
    """Test updating stock with invalid item ID"""
    client.force_login(user)
    data = {
        "item_id": 99999,  # Non-existent ID
        "delta_qty": 5,
    }
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302


def test_add_inventory_view_invalid_data(client, admin_user, product):
    """Test adding inventory with invalid data"""
    client.force_login(admin_user)
    data = {
        "product": product.id,
        "location": 99999,  # Invalid location ID
        "quantity": 5,
        "barcode": "123456789012",
    }
    response = client.post(reverse("inventory:add_inventory"), data)
    assert response.status_code == 200  # Returns form with errors


def test_remove_product_with_stock(client, admin_user, inventory_item):
    """Test removing a product that has stock"""
    client.force_login(admin_user)
    data = {"product": inventory_item.product.id}
    response = client.post(reverse("inventory:remove_product"), data)
    assert response.status_code == 302
    inventory_item.product.refresh_from_db()
    assert not inventory_item.product.active
    inventory_item.refresh_from_db()
    assert inventory_item.active  # Item should stay active until quantity is 0


def test_add_product_duplicate(client, admin_user, product):
    """Test adding a duplicate product"""
    client.force_login(admin_user)
    data = {"name": product.name, "manufacturer": product.manufacturer}
    response = client.post(reverse("inventory:add_product"), data)
    assert response.status_code == 200  # Returns form with errors


def test_stock_check_empty_location(client, user, location):
    """Test stock check with empty location"""
    client.force_login(user)
    response = client.get(reverse("inventory:stock_check"))
    assert response.status_code == 200
    items_in_location = response.context["items_in_location"]
    assert location in items_in_location
    assert len(items_in_location[location]) == 0


def test_index_view_with_recent_orders(client, admin_user, inventory_item):
    """Test index view with recent orders for staff"""
    client.force_login(admin_user)
    response = client.get(reverse("inventory:index"))
    assert response.status_code == 200
    assert "recent_orders" in response.context
