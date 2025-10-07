import pytest
from inventory.forms import (
    AddProductForm,
    AddLocationForm,
    AddInventoryForm,
    InventoryQuantityUpdateForm,
    DeactivateLocationForm,
    DeactivateProductForm,
)
from inventory.models import Product, Location, Inventory
from inventory.barcode_gen import barcode_page_generation

pytestmark = pytest.mark.django_db


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


def test_product_form_valid():
    """Test valid product form"""
    form = AddProductForm(
        {
            "name": "New Item",
            "manufacturer": "New Manufacturer",
            "barcode": "123456789012",  # Valid UPC-A barcode
        }
    )
    assert form.is_valid()


def test_product_form_invalid_barcode():
    """Test invalid product form"""
    form = AddProductForm(
        {"name": "New Item", "manufacturer": "New Manufacturer", "barcode": "nope"}
    )
    assert not form.is_valid()


def test_product_form_duplicate():
    """Test duplicate product form"""
    Product.objects.create(name="Test", manufacturer="Test")
    form = AddProductForm({"name": "Test", "manufacturer": "Test"})
    assert not form.is_valid()
    assert "already exists" in str(form.errors)


def test_location_form_valid():
    """Test valid location form"""
    form = AddLocationForm({"name": "New Location"})
    assert form.is_valid()


def test_location_form_duplicate():
    """Test duplicate location form"""
    Location.objects.create(name="Test")
    form = AddLocationForm({"name": "Test"})
    assert not form.is_valid()
    assert "already exists" in str(form.errors)


def test_add_inventory_form_valid(product, location):
    """Test valid add inventory form"""
    form = AddInventoryForm(
        {
            "product": product.id,
            "location": location.id,
            "quantity": 5,
            "barcode": "123456789012",
        }
    )
    assert form.is_valid()


def test_stock_update_form_valid(inventory_item):
    """Test valid stock update form"""
    form = InventoryQuantityUpdateForm({"item_id": inventory_item.id, "delta_qty": 5})
    assert form.is_valid()


def test_stock_update_form_negative(inventory_item):
    """Test stock update form with negative quantity"""
    form = InventoryQuantityUpdateForm(
        {
            "item_id": inventory_item.id,
            "delta_qty": -5,  # Less than current quantity (10)
        }
    )
    assert form.is_valid()  # Form should be valid, view handles the validation


def test_remove_location_form_valid(location):
    """Test valid remove location form"""
    form = DeactivateLocationForm({"location": location.id})
    assert form.is_valid()


def test_deactivate_product_form_valid(product):
    """Test valid deactivate product form"""
    form = DeactivateProductForm({"product": product.id})
    assert form.is_valid()


def test_barcode_generation():
    """Test barcode page generation"""
    # Create some inventory items
    product = Product.objects.create(
        name="Test", manufacturer="Test", barcode="123456789012"
    )
    location = Location.objects.create(name="Test")
    Inventory.objects.create(product=product, location=location, quantity=10)

    # Generate barcode page with minimal dimensions
    result = barcode_page_generation(rows=1, cols=1, pages=1)
    assert result is not None
    assert isinstance(result, bytes)  # Should return PDF bytes
    assert result.startswith(b"%PDF")  # Should be a PDF file
