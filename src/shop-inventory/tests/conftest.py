"""Root conftest.py for shop-inventory tests.

Contains common fixtures used across multiple test modules.
"""

import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user():
    """Create a standard user for testing."""
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def admin_user():
    """Create a superuser for testing."""
    User = get_user_model()
    return User.objects.create_superuser(username="admin", password="adminpass")


@pytest.fixture
def location():
    """Create a standard location for testing."""
    from inventory.models import Location

    return Location.objects.create(name="Test Location")


@pytest.fixture
def shopfloor():
    """Create or get the Shopfloor location for testing.

    Uses get_or_create to avoid conflicts when multiple tests use this fixture.
    """
    from inventory.models import Location

    location, _ = Location.objects.get_or_create(name="Shopfloor")
    return location


@pytest.fixture
def product():
    """Create a standard product with barcode for testing."""
    from inventory.models import Product

    return Product.objects.create(
        name="Test Item",
        manufacturer="Test Manufacturer",
        barcode="123456789012",
    )


@pytest.fixture
def inactive_product():
    """Create an inactive product for testing."""
    from inventory.models import Product

    product = Product.objects.create(
        name="Inactive Item",
        manufacturer="Test Manufacturer",
        barcode="999999999999",
    )
    product.active = False
    product.save()
    return product


@pytest.fixture
def inventory_item(product, shopfloor):
    """Create a standard inventory item for testing.

    Depends on product and shopfloor fixtures.
    """
    from inventory.models import Inventory

    return Inventory.objects.create(
        product=product,
        location=shopfloor,
        quantity=10,
    )
