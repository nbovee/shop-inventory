import pytest
from django.core.exceptions import ValidationError
from inventory.models import (
    Product,
    Location,
    Inventory,
    normalize_barcode,
    barcode_is_uuid,
)

pytestmark = pytest.mark.django_db


def test_normalize_barcode_number_system_2():
    """Test normalize_barcode with number system 2 (variable weight items)"""
    barcode = "290123456789"  # Starts with 2
    normalized = normalize_barcode(barcode)
    assert normalized == "290123000000"


def test_normalize_barcode_regular():
    """Test normalize_barcode with regular UPC-A"""
    barcode = "123456789012"  # Does not start with 2
    normalized = normalize_barcode(barcode)
    assert normalized == "123456789012"


def test_barcode_is_uuid_valid():
    """Test UUID barcode validation"""
    uuid_barcode = "12345678901234567890123456789012"  # 32 hex digits
    assert barcode_is_uuid(uuid_barcode)


def test_barcode_is_uuid_invalid():
    """Test invalid UUID barcode"""
    assert not barcode_is_uuid("invalid")


def test_product_normalized_barcode_saved():
    """Test that normalized_barcode is set on save"""
    product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="290123456789",
    )
    assert product.normalized_barcode == "290123000000"


def test_location_str():
    """Test Location __str__ method"""
    location = Location.objects.create(name="Test Location")
    assert str(location) == "Test Location"


def test_inventory_str():
    """Test Inventory __str__ method"""
    product = Product.objects.create(
        name="Test Item",
        manufacturer="Test Manufacturer",
        barcode="123456789012",
    )
    location = Location.objects.create(name="Test Location")
    inventory = Inventory.objects.create(
        product=product,
        location=location,
        quantity=10,
    )
    expected = "Test Item (Test Manufacturer) @ Test Location"
    assert str(inventory) == expected
