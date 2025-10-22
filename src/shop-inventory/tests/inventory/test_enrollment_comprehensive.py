"""
Comprehensive enrollment tests that mimic actual user workflows with session handling.

These tests verify the complete multi-step enrollment process following the exact
session state management that real users experience through the web interface.
"""

import pytest
from django.urls import reverse
from inventory.models import Product, Location, Inventory


pytestmark = pytest.mark.django_db


def test_enrollment_upc_a_type_2_normalization_same_product(
    client, admin_user, location
):
    """
    Test that two UPC-A type 2 barcodes with different tails normalize to same product.

    This verifies that variable-weight items (number system 2) correctly normalize
    the weight/price portion to zeros, allowing different scans of the same item
    to update the same product record.
    """
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # First enrollment with barcode "234567123456"
    # Step 1: Select location
    response = client.post(
        url, {"action": "select_location", "location_id": location.id}
    )
    assert response.status_code == 200
    assert int(client.session["selected_location_id"]) == location.id
    assert response.context["form_type"] == "scan_form"

    # Step 2: Scan first barcode
    first_barcode = "234567123456"
    response = client.post(url, {"action": "scan_barcode", "barcode": first_barcode})
    assert response.status_code == 200
    assert client.session["current_barcode"] == first_barcode
    assert response.context["form_type"] == "new_item_form"

    # Step 3: Add product info (NO barcode in POST - comes from session)
    response = client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Variable Weight Item",
            "manufacturer": "TestCo",
        },
    )
    assert response.status_code == 200
    assert response.context["form_type"] == "quantity_form"
    assert "current_product_id" in client.session

    # Verify product created with normalized barcode
    product = Product.objects.get(name="Variable Weight Item")
    assert product.barcode == first_barcode
    assert product.normalized_barcode == "234567000000"

    # Step 4: Add quantity
    response = client.post(url, {"action": "add_quantity", "quantity": 5})
    assert response.status_code == 200
    assert response.context["form_type"] == "scan_form"

    # Verify inventory created
    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 5

    # Session should clear product data but keep location
    assert "current_product_id" not in client.session
    assert "current_barcode" not in client.session
    assert int(client.session["selected_location_id"]) == location.id

    # Second scan with different tail digits
    # Step 5: Scan second barcode with same item code but different weight/price
    second_barcode = "234567654321"
    response = client.post(url, {"action": "scan_barcode", "barcode": second_barcode})
    assert response.status_code == 200

    # Should find EXISTING product and show quantity form (not new item form)
    assert response.context["form_type"] == "quantity_form"
    assert response.context["product"] == product
    assert client.session["current_product_id"] == product.id

    # Step 6: Add more quantity
    response = client.post(url, {"action": "add_quantity", "quantity": 3})
    assert response.status_code == 200
    assert response.context["form_type"] == "scan_form"

    # Verify SAME inventory record updated, not duplicated
    inventory.refresh_from_db()
    assert inventory.quantity == 8
    assert Inventory.objects.filter(product=product, location=location).count() == 1

    # Verify only ONE product was created
    assert Product.objects.filter(name="Variable Weight Item").count() == 1


def test_enrollment_upc_a_generic(client, admin_user, location):
    """Test full enrollment workflow with standard UPC-A barcode."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # Step 1: Select location
    response = client.post(
        url, {"action": "select_location", "location_id": location.id}
    )
    assert response.status_code == 200

    # Step 2: Scan UPC-A barcode (number system 0)
    barcode = "012345678901"
    response = client.post(url, {"action": "scan_barcode", "barcode": barcode})
    assert response.status_code == 200
    assert response.context["form_type"] == "new_item_form"

    # Step 3: Add product info
    response = client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Standard UPC Item",
            "manufacturer": "Brand A",
        },
    )
    assert response.status_code == 200
    assert response.context["form_type"] == "quantity_form"

    # Verify product created without normalization
    product = Product.objects.get(name="Standard UPC Item")
    assert product.barcode == barcode
    assert product.normalized_barcode == barcode  # No normalization for non-type-2

    # Step 4: Add quantity
    response = client.post(url, {"action": "add_quantity", "quantity": 10})
    assert response.status_code == 200

    # Verify inventory
    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 10


def test_enrollment_upc_e(client, admin_user, location):
    """Test full enrollment workflow with UPC-E barcode."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # Complete workflow with 8-digit UPC-E
    client.post(url, {"action": "select_location", "location_id": location.id})

    barcode = "01234567"
    response = client.post(url, {"action": "scan_barcode", "barcode": barcode})
    assert response.status_code == 200
    assert response.context["form_type"] == "new_item_form"

    response = client.post(
        url,
        {
            "action": "add_new_item",
            "name": "UPC-E Item",
            "manufacturer": "Compact Brand",
        },
    )
    assert response.status_code == 200

    product = Product.objects.get(name="UPC-E Item")
    assert product.barcode == barcode
    assert len(product.barcode) == 8

    response = client.post(url, {"action": "add_quantity", "quantity": 7})
    assert response.status_code == 200

    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 7


def test_enrollment_uuid(client, admin_user, location):
    """Test full enrollment workflow with UUID barcode."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # Complete workflow with 32-character hex UUID
    client.post(url, {"action": "select_location", "location_id": location.id})

    barcode = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    response = client.post(url, {"action": "scan_barcode", "barcode": barcode})
    assert response.status_code == 200
    assert response.context["form_type"] == "new_item_form"

    response = client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Custom UUID Item",
            "manufacturer": "No Barcode Co",
        },
    )
    assert response.status_code == 200

    product = Product.objects.get(name="Custom UUID Item")
    assert product.barcode == barcode
    assert len(product.barcode) == 32

    response = client.post(url, {"action": "add_quantity", "quantity": 2})
    assert response.status_code == 200

    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 2


def test_enrollment_non_barcode_item(client, admin_user, location):
    """Test the separate non-barcode item enrollment workflow."""
    client.force_login(admin_user)
    url = reverse("inventory:add_product")

    # First submission - creates new product with auto-generated UUID barcode
    response = client.post(
        url,
        {
            "name": "Non-Barcode Item",
            "manufacturer": "Local Maker",
            "location": location.id,
            "quantity": 15,
        },
    )
    assert response.status_code == 302  # Redirects on success

    # Verify product created with UUID barcode
    product = Product.objects.get(name="Non-Barcode Item", manufacturer="Local Maker")
    assert len(product.barcode) == 32  # UUID hex string
    assert product.normalized_barcode == product.barcode

    # Verify inventory
    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 15

    # Second submission with same name/manufacturer - should update quantity
    response = client.post(
        url,
        {
            "name": "Non-Barcode Item",
            "manufacturer": "Local Maker",
            "location": location.id,
            "quantity": 10,
        },
    )
    assert response.status_code == 302

    # Should NOT create duplicate product
    assert (
        Product.objects.filter(
            name="Non-Barcode Item", manufacturer="Local Maker"
        ).count()
        == 1
    )

    # Should update inventory quantity
    inventory.refresh_from_db()
    assert inventory.quantity == 25


def test_rescan_existing_product_updates_quantity(client, admin_user, location):
    """Test that re-scanning an existing barcode at the same location updates quantity."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # First enrollment - create product
    client.post(url, {"action": "select_location", "location_id": location.id})

    barcode = "111222333444"
    client.post(url, {"action": "scan_barcode", "barcode": barcode})
    client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Rescan Test Item",
            "manufacturer": "TestCo",
        },
    )
    client.post(url, {"action": "add_quantity", "quantity": 5})

    product = Product.objects.get(name="Rescan Test Item")
    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 5

    # Session should have cleared product data but kept location
    assert "current_product_id" not in client.session
    assert int(client.session["selected_location_id"]) == location.id

    # Re-scan the SAME barcode
    response = client.post(url, {"action": "scan_barcode", "barcode": barcode})
    assert response.status_code == 200

    # Should find existing product and show quantity form (not new item form)
    assert response.context["form_type"] == "quantity_form"
    assert response.context["product"] == product

    # Add more quantity
    response = client.post(url, {"action": "add_quantity", "quantity": 8})
    assert response.status_code == 200

    # Verify quantity updated, not duplicated
    inventory.refresh_from_db()
    assert inventory.quantity == 13
    assert Inventory.objects.filter(product=product, location=location).count() == 1


def test_rescan_existing_product_different_location(
    client, admin_user, location, shopfloor
):
    """Test that scanning existing product at different location creates separate inventory."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # Create product at first location
    client.post(url, {"action": "select_location", "location_id": location.id})

    barcode = "555666777888"
    client.post(url, {"action": "scan_barcode", "barcode": barcode})
    client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Multi-Location Item",
            "manufacturer": "Everywhere Co",
        },
    )
    client.post(url, {"action": "add_quantity", "quantity": 10})

    product = Product.objects.get(name="Multi-Location Item")

    # Clear workflow and select different location
    client.post(url, {"action": "cancel"})
    assert "selected_location_id" not in client.session

    # Start fresh with second location
    client.post(url, {"action": "select_location", "location_id": shopfloor.id})

    # Scan same barcode
    response = client.post(url, {"action": "scan_barcode", "barcode": barcode})
    assert response.status_code == 200

    # Should find existing product
    assert response.context["form_type"] == "quantity_form"
    assert response.context["product"] == product

    # Add quantity at new location
    response = client.post(url, {"action": "add_quantity", "quantity": 5})
    assert response.status_code == 200

    # Verify two separate inventory records
    assert Inventory.objects.filter(product=product).count() == 2

    inventory_location1 = Inventory.objects.get(product=product, location=location)
    assert inventory_location1.quantity == 10

    inventory_location2 = Inventory.objects.get(product=product, location=shopfloor)
    assert inventory_location2.quantity == 5


def test_invalid_session_state_redirects(client, admin_user, location):
    """Test that invalid session states properly redirect to restart workflow."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # Try to add new item without selecting location first
    response = client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Test",
            "manufacturer": "Test",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("inventory:add_item_to_location")

    # Select location but skip barcode scan
    client.post(url, {"action": "select_location", "location_id": location.id})

    response = client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Test",
            "manufacturer": "Test",
        },
    )
    assert response.status_code == 302

    # Try to add quantity without product_id
    response = client.post(url, {"action": "add_quantity", "quantity": 5})
    assert response.status_code == 302


def test_session_persistence_across_multiple_items(client, admin_user, location):
    """Test that location persists while scanning multiple items in sequence."""
    client.force_login(admin_user)
    url = reverse("inventory:add_item_to_location")

    # Select location once
    client.post(url, {"action": "select_location", "location_id": location.id})

    # Add first item
    client.post(url, {"action": "scan_barcode", "barcode": "111111111111"})
    client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Item One",
            "manufacturer": "Brand A",
        },
    )
    client.post(url, {"action": "add_quantity", "quantity": 3})

    # Location should still be in session
    assert int(client.session["selected_location_id"]) == location.id

    # Add second item without re-selecting location
    client.post(url, {"action": "scan_barcode", "barcode": "222222222222"})
    client.post(
        url,
        {
            "action": "add_new_item",
            "name": "Item Two",
            "manufacturer": "Brand B",
        },
    )
    client.post(url, {"action": "add_quantity", "quantity": 7})

    # Verify both items created at same location
    item1 = Product.objects.get(name="Item One")
    item2 = Product.objects.get(name="Item Two")

    assert Inventory.objects.filter(location=location).count() == 2
    assert Inventory.objects.get(product=item1, location=location).quantity == 3
    assert Inventory.objects.get(product=item2, location=location).quantity == 7
