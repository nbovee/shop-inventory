import pytest
from inventory.forms import (
    BaseItemForm,
    LocationForm,
    AddInventoryForm,
    EditInventoryForm,
    StockUpdateForm,
    RemoveLocationForm,
    DeactivateBaseItemForm,
)
from inventory.models import Product, Location, InventoryEntry
from inventory.barcode_gen import barcode_page_generation

pytestmark = pytest.mark.django_db


@pytest.fixture
def base_item():
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
def inventory_item(base_item, location):
    return InventoryEntry.objects.create(
        base_item=base_item,
        location=location,
        quantity=10,
    )


def test_base_item_form_valid():
    """Test valid base item form"""
    form = BaseItemForm({"name": "New Item", "manufacturer": "New Manufacturer"})
    assert form.is_valid()


def test_base_item_form_duplicate():
    """Test duplicate base item form"""
    Product.objects.create(name="Test", manufacturer="Test")
    form = BaseItemForm({"name": "Test", "manufacturer": "Test"})
    assert not form.is_valid()
    assert "already exists" in str(form.errors)


def test_location_form_valid():
    """Test valid location form"""
    form = LocationForm({"name": "New Location"})
    assert form.is_valid()


def test_location_form_duplicate():
    """Test duplicate location form"""
    Location.objects.create(name="Test")
    form = LocationForm({"name": "Test"})
    assert not form.is_valid()
    assert "already exists" in str(form.errors)


def test_add_inventory_form_valid(base_item, location):
    """Test valid add inventory form"""
    form = AddInventoryForm(
        {
            "base_item": base_item.id,
            "location": location.id,
            "quantity": 5,
            "barcode": "123456789012",
        }
    )
    assert form.is_valid()


def test_add_inventory_form_invalid_barcode():
    """Test invalid barcode in add inventory form"""
    form = AddInventoryForm(
        {
            "base_item": 1,
            "location": 1,
            "quantity": 5,
            "barcode": "invalid",  # Invalid barcode format
        }
    )
    assert not form.is_valid()
    assert "barcode" in form.errors


def test_edit_inventory_form_valid(inventory_item):
    """Test valid edit inventory form"""
    form = EditInventoryForm(
        {
            "base_item": inventory_item.base_item.id,
            "location": inventory_item.location.id,
            "quantity": 15,
            "barcode": inventory_item.barcode,
        },
        instance=inventory_item,
    )
    assert form.is_valid()


def test_stock_update_form_valid(inventory_item):
    """Test valid stock update form"""
    form = StockUpdateForm({"item_id": inventory_item.id, "delta_qty": 5})
    assert form.is_valid()


def test_stock_update_form_negative(inventory_item):
    """Test stock update form with negative quantity"""
    form = StockUpdateForm(
        {
            "item_id": inventory_item.id,
            "delta_qty": -5,  # Less than current quantity (10)
        }
    )
    assert form.is_valid()  # Form should be valid, view handles the validation


def test_remove_location_form_valid(location):
    """Test valid remove location form"""
    form = RemoveLocationForm({"location": location.id})
    assert form.is_valid()


def test_remove_base_item_form_valid(base_item):
    """Test valid remove base item form"""
    form = DeactivateBaseItemForm({"base_item": base_item.id})
    assert form.is_valid()


def test_barcode_generation():
    """Test barcode page generation"""
    # Create some inventory items
    base_item = Product.objects.create(name="Test", manufacturer="Test")
    location = Location.objects.create(name="Test")
    InventoryEntry.objects.create(
        base_item=base_item, location=location, quantity=10, barcode="123456789012"
    )

    # Generate barcode page with minimal dimensions and dry run
    result = barcode_page_generation(rows=1, cols=1, dry_run=True)
    assert result is not None
    assert isinstance(result, bytes)  # Should return PDF bytes
    assert result.startswith(b"%PDF")  # Should be a PDF file
