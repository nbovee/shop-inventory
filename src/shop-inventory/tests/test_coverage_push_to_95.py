"""Comprehensive tests to reach 95%+ coverage by testing all missing code paths"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from inventory.models import Product, Location, Inventory
from checkout.models import Order
from checkout.forms import AddToCartForm, ProcessOrderForm
from inventory.forms import (
    AddInventoryForm,
    InventoryQuantityUpdateForm,
    ReactivateProductForm,
)

pytestmark = pytest.mark.django_db


# ============ Test checkout/forms.py missing lines ============


def test_add_to_cart_form_with_barcode(inventory_item):
    """Test AddToCartForm with valid barcode (lines 30-37)"""
    form = AddToCartForm(
        data={"barcode": inventory_item.product.barcode, "quantity": 1},
        cart={},
    )
    assert form.is_valid()
    cart = form.save()
    assert str(inventory_item.id) in cart


def test_add_to_cart_form_with_invalid_barcode():
    """Test AddToCartForm with barcode that doesn't exist"""
    form = AddToCartForm(
        data={"barcode": "111111111111", "quantity": 1},
        cart={},
    )
    assert not form.is_valid()
    assert "Product not found" in str(form.errors)


def test_process_order_form_insufficient_stock(inventory_item):
    """Test ProcessOrderForm when inventory quantity is insufficient (line 109)"""
    # Try to order more than available
    cart = {str(inventory_item.id): inventory_item.quantity + 10}

    form = ProcessOrderForm(
        data={"implicit_id": "test@rowan.edu"},
        cart=cart,
        request=None,
    )
    assert form.is_valid()  # Form validation passes

    # But saving should raise ValidationError
    with pytest.raises(Exception):  # Will raise ValidationError
        form.save()


def test_process_order_form_inventory_does_not_exist():
    """Test ProcessOrderForm when inventory item no longer exists (lines 124-125)"""
    cart = {"99999": 5}  # Non-existent inventory ID

    form = ProcessOrderForm(
        data={"implicit_id": "test@rowan.edu"},
        cart=cart,
        request=None,
    )
    assert form.is_valid()

    # Saving should raise ValidationError
    with pytest.raises(Exception):
        form.save()


# ============ Test checkout/views.py missing lines ============


def test_checkout_barcode_scan_exception(client, shopfloor):
    """Test barcode scanning exception path (lines 43-45)"""
    # Create a condition that will trigger exception
    product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="123456789012",
    )
    # Don't create inventory - this will trigger the "No item found" path
    Inventory.objects.create(product=product, location=shopfloor, quantity=5)

    session = client.session
    session["cart"] = {}
    session.save()

    data = {"barcode": "999999999999"}  # Non-existent barcode
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302


def test_checkout_normal_add_exception(client, inventory_item):
    """Test normal add to cart exception path (lines 54-55)"""
    session = client.session
    session["cart"] = {}
    session.save()

    # Use a product_id that will cause an issue
    data = {
        "product_id": "invalid",  # Invalid type
        "quantity": 1,
        "barcode": "",
    }
    response = client.post(reverse("checkout:index"), data)
    assert response.status_code == 302


def test_process_order_exception_path(client, inventory_item):
    """Test process order exception handling (lines 114-115)"""
    session = client.session
    session["cart"] = {str(inventory_item.id): inventory_item.quantity + 100}
    session.save()

    data = {"implicit_id": "test@rowan.edu"}
    response = client.post(reverse("checkout:process_order"), data)
    assert response.status_code == 302


def test_process_order_duplicate_errors(client, inventory_item):
    """Test process order with both error loops (line 120)"""
    session = client.session
    session["cart"] = {str(inventory_item.id): 2}
    session.save()

    # Submit without implicit_id to trigger form errors
    data = {"implicit_id": ""}
    response = client.post(reverse("checkout:process_order"), data)
    assert response.status_code == 302


# ============ Test inventory/forms.py missing lines ============


def test_add_inventory_form_reactivate_inactive(inactive_product, location):
    """Test AddInventoryForm reactivating inactive item (lines 96-98)"""
    # First create an inactive inventory item
    inventory = Inventory.objects.create(
        product=inactive_product,
        location=location,
        quantity=5,
    )

    # Now try to add to same location with the same product
    form = AddInventoryForm(
        {
            "product": inactive_product.id,
            "location": location.id,
            "quantity": 10,
            "barcode": inactive_product.barcode,
        }
    )

    # This should trigger the reactivate path
    # The form validation will raise ValidationError with code='reactivated'
    assert not form.is_valid() or form.errors


def test_add_inventory_form_update_existing(product, location):
    """Test AddInventoryForm updating existing item (lines 109-111)"""
    # Create existing inventory
    Inventory.objects.create(product=product, location=location, quantity=5)

    # Try to add more to the same location
    form = AddInventoryForm(
        {
            "product": product.id,
            "location": location.id,
            "quantity": 10,
            "barcode": product.barcode,
        }
    )

    # Should trigger the update existing item path
    assert not form.is_valid() or form.errors


def test_inventory_quantity_update_form_inactive_product(inventory_item):
    """Test InventoryQuantityUpdateForm with inactive product (line 143)"""
    # Make product inactive
    inventory_item.product.active = False
    inventory_item.product.save()

    form = InventoryQuantityUpdateForm(
        {
            "item_id": inventory_item.id,
            "delta_qty": 5,  # Try to add quantity
        }
    )

    assert not form.is_valid()
    assert "inactive" in str(form.errors).lower()


def test_reactivate_product_form_save(inactive_product):
    """Test ReactivateProductForm save method (lines 224-226)"""
    form = ReactivateProductForm({"product": inactive_product.id})
    assert form.is_valid()

    product = form.save()
    product.refresh_from_db()
    assert product.active


def test_edit_product_form_duplicate_check(product):
    """Test EditProductForm duplicate validation (line 270)"""
    # Create another product
    Product.objects.create(
        name="Duplicate",
        manufacturer="Test",
        barcode="111111111111",
    )

    # Try to edit first product to have same name/manufacturer as second
    from inventory.forms import EditProductForm

    form = EditProductForm(
        {"name": "Duplicate", "manufacturer": "Test"},
        instance=product,
    )

    assert not form.is_valid()


# ============ Test inventory/views.py missing lines ============


def test_stock_update_inactive_product_quantity_zero(client, admin_user, location):
    """Test stock update with inactive product reaching zero (line 80)"""
    # Create product and make it inactive
    product = Product.objects.create(
        name="Test",
        manufacturer="Test",
        barcode="123456789012",
    )
    product.active = False
    product.save()

    inventory = Inventory.objects.create(product=product, location=location, quantity=5)

    client.force_login(admin_user)
    data = {"item_id": inventory.id, "delta_qty": -5}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302


def test_stock_update_exception(client, admin_user, inventory_item):
    """Test stock update exception handling (lines 96-97)"""
    client.force_login(admin_user)

    # Create a scenario that triggers an exception
    data = {"item_id": inventory_item.id, "delta_qty": "invalid"}
    response = client.post(reverse("inventory:stock_update"), data)
    assert response.status_code == 302


def test_add_location_validation_error(client, admin_user):
    """Test add location ValidationError handling (lines 198-202)"""
    # Create an inactive location
    location = Location.objects.create(name="TestLoc")
    location.active = False
    location.save()

    client.force_login(admin_user)
    data = {"name": "TestLoc"}
    response = client.post(reverse("inventory:add_location"), data)
    # Should handle the validation error and redirect
    assert response.status_code in [200, 302]


def test_add_item_get_request_with_location_in_session(client, admin_user, location):
    """Test add_item_to_location GET with location in session (line 259)"""
    client.force_login(admin_user)

    # Set location in session
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    # GET request should continue with location
    response = client.get(reverse("inventory:add_item_to_location"))
    assert response.status_code == 200


def test_add_item_continue_with_location(client, admin_user, location):
    """Test add_item_to_location session continuation (line 314)"""
    client.force_login(admin_user)

    # Set location in session first
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    # Now do a scan action
    data = {"action": "scan_barcode", "barcode": "123456789012"}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 200


def test_add_item_location_does_not_exist(client, admin_user):
    """Test add_item exception for invalid location (lines 331-332)"""
    client.force_login(admin_user)

    # Try to select an invalid location
    data = {"action": "select_location", "location_id": 99999}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should catch the exception and redirect
    assert response.status_code in [302, 404]


def test_add_item_inactive_product_warning(
    client, admin_user, location, inactive_product
):
    """Test scanning inactive product (lines 367-374)"""
    client.force_login(admin_user)

    # Set location in session
    session = client.session
    session["selected_location_id"] = location.id
    session.save()

    # Scan the inactive product's barcode
    data = {"action": "scan_barcode", "barcode": inactive_product.barcode}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    assert response.status_code == 200


def test_add_item_quantity_exception(client, admin_user, location, product):
    """Test add quantity exception handling (lines 502-509)"""
    client.force_login(admin_user)

    # Set up session
    session = client.session
    session["selected_location_id"] = location.id
    session["current_product_id"] = product.id
    session.save()

    # Try to add invalid quantity
    data = {"action": "add_quantity", "quantity": -999}
    response = client.post(reverse("inventory:add_item_to_location"), data)
    # Should handle the error
    assert response.status_code == 200


# ============ Test model methods ============


def test_product_activate_method(inactive_product):
    """Test Product.activate() method"""
    inactive_product.activate()
    assert inactive_product.active


def test_location_activate_method():
    """Test Location.activate() method"""
    location = Location.objects.create(name="Test")
    location.active = False
    location.save()

    location.activate()
    assert location.active


def test_inventory_activate_method(inventory_item):
    """Test Inventory.activate() method (no-op)"""
    # This method exists but doesn't do anything
    inventory_item.activate()
    # Just verify it doesn't crash
