import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from inventory.models import Product, Location, Inventory
from checkout.models import Order, OrderItem

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
def staff_user():
    User = get_user_model()
    user = User.objects.create_user(
        username="staffuser",
        password="staffpass123",
        is_staff=True,
    )
    # Add necessary permissions
    permission = Permission.objects.get(codename="add_product")
    user.user_permissions.add(permission)
    return user


@pytest.fixture
def floor_location():
    return Location.objects.create(
        name="Floor",
    )


@pytest.fixture
def product():
    return Product.objects.create(
        name="Test Item",
        manufacturer="Test Manufacturer",
    )


@pytest.fixture
def inventory_item(product, floor_location):
    return Inventory.objects.create(
        product=product,
        location=floor_location,
        quantity=10,
    )


@pytest.fixture
def cart_session():
    return {}


def test_index_view(client, inventory_item):
    """Test the checkout index view"""
    response = client.get(reverse("checkout:index"))
    assert response.status_code == 200
    assert inventory_item in response.context["inventory_items"]


def test_index_view_with_filter(client, inventory_item):
    """Test the checkout index view with filter"""
    response = client.get(reverse("checkout:index") + "?filter=Test")
    assert response.status_code == 200
    assert inventory_item in response.context["inventory_items"]


def test_add_to_cart(client, inventory_item):
    """Test adding item to cart"""
    # Initialize session
    session = client.session
    session["cart"] = {}
    session.save()

    data = {
        "product_id": inventory_item.id,
        "quantity": 1,
        "barcode": "",  # Empty barcode to use product_id
    }
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302

    # Refresh session data
    cart = client.session.get("cart", {})
    assert str(inventory_item.id) in cart
    assert cart[str(inventory_item.id)] == 1


def test_add_to_cart_exceeding_quantity(client, inventory_item):
    """Test adding more items than available"""
    # Initialize session
    session = client.session
    session["cart"] = {}
    session.save()

    data = {
        "product_id": inventory_item.id,
        "quantity": inventory_item.quantity + 1,
        "barcode": "",
    }
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302

    # Cart should be empty as the request should fail
    cart = client.session.get("cart", {})
    assert not cart


def test_process_order(client, inventory_item):
    """Test processing an order"""
    # Initialize session with cart data
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.modified = True  # Mark session as modified
    session.save()

    # Process the order
    order_data = {
        "implicit_id": "test_customer@rowan.edu"  # Using valid email format
    }
    initial_quantity = inventory_item.quantity
    response = client.post(reverse("checkout:process_order"), order_data)
    assert response.status_code == 302

    # Check if order was created
    assert Order.objects.filter(implicit_id="test_customer@rowan.edu").exists()
    order = Order.objects.get(implicit_id="test_customer@rowan.edu")
    assert OrderItem.objects.filter(order=order).exists()

    # Check if inventory was updated
    inventory_item.refresh_from_db()
    assert inventory_item.quantity == initial_quantity - 2

    # Check if cart was cleared
    assert "cart" not in client.session


def test_recent_orders_view(client, staff_user):
    """Test the recent orders view"""
    client.force_login(staff_user)
    response = client.get(reverse("checkout:recent_orders"))
    assert response.status_code == 200


def test_recent_orders_view_unauthorized(client, user):
    """Test the recent orders view with unauthorized user"""
    client.force_login(user)
    response = client.get(reverse("checkout:recent_orders"))
    assert response.status_code == 403  # Should be forbidden


def test_cart_manipulation(client, inventory_item):
    """Test multiple cart operations"""
    # Initialize session
    session = client.session
    session["cart"] = {}
    session.save()

    # Add item to cart
    data1 = {"product_id": inventory_item.id, "quantity": 2, "barcode": ""}
    client.post(reverse("checkout:index"), data1)

    # Update quantity
    data2 = {"product_id": inventory_item.id, "quantity": 1, "barcode": ""}
    client.post(reverse("checkout:index"), data2)

    # Refresh session data
    cart = client.session.get("cart", {})
    assert str(inventory_item.id) in cart
    assert cart[str(inventory_item.id)] == 3  # Should be cumulative
