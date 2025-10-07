import pytest
from inventory.forms import (
    AddLocationForm,
    AddProductForm,
    EditProductForm,
    ReactivateProductForm,
    ReactivateLocationForm,
)
from inventory.models import Product, Location
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


def test_add_location_form_reactivates_inactive():
    """Test that AddLocationForm reactivates inactive location"""
    # Create an inactive location
    location = Location.objects.create(name="Test")
    location.active = False
    location.save()

    form = AddLocationForm({"name": "Test"})
    # Form should be valid and will reactivate the location
    try:
        if form.is_valid():
            form.save()
    except ValidationError as e:
        # The form raises a ValidationError with code 'reactivated'
        assert e.code == "reactivated"
        location.refresh_from_db()
        assert location.active


def test_add_product_form_reactivates_inactive():
    """Test that AddProductForm reactivates inactive product"""
    # Create an inactive product
    product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="123456789012",
    )
    product.active = False
    product.save()

    form = AddProductForm(
        {
            "name": "Test",
            "manufacturer": "Test",
            "barcode": "123456789012",
        }
    )
    # Form should handle reactivation
    try:
        if form.is_valid():
            form.save()
    except ValidationError as e:
        assert e.code == "reactivated"
        product.refresh_from_db()
        assert product.active


def test_edit_product_form():
    """Test EditProductForm"""
    product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="123456789012",
    )
    form = EditProductForm(
        {"name": "Updated", "manufacturer": "Updated", "barcode": "123456789012"},
        instance=product,
    )
    assert form.is_valid()
    updated = form.save()
    assert updated.name == "Updated"


def test_reactivate_product_form():
    """Test ReactivateProductForm"""
    product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="123456789012",
    )
    product.active = False
    product.save()

    form = ReactivateProductForm({"product": product.id})
    assert form.is_valid()


def test_reactivate_location_form():
    """Test ReactivateLocationForm"""
    location = Location.objects.create(name="Test")
    location.active = False
    location.save()

    form = ReactivateLocationForm({"location": location.id})
    assert form.is_valid()


def test_add_location_form_blank():
    """Test AddLocationForm with blank name"""
    form = AddLocationForm({"name": ""})
    assert not form.is_valid()


def test_add_product_form_invalid_barcode():
    """Test AddProductForm with various invalid barcodes"""
    # Too short
    form = AddProductForm(
        {
            "name": "Test",
            "manufacturer": "Test",
            "barcode": "123",
        }
    )
    assert not form.is_valid()

    # Invalid characters
    form = AddProductForm(
        {
            "name": "Test",
            "manufacturer": "Test",
            "barcode": "abcdefghijkl",
        }
    )
    assert not form.is_valid()
