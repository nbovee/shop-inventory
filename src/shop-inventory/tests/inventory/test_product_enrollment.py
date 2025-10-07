import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, Location, Inventory

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


def test_enrollment_step_1_select_location(client, admin_user, location):
    """Test step 1: Location selection shows barcode scan form"""
    client.force_login(admin_user)

    response = client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "select_location", "location_id": location.id},
    )

    assert response.status_code == 200
    assert "form_type" in response.context
    assert response.context["form_type"] == "scan_form"
    assert response.context["selected_location"] == location


def test_enrollment_step_2_scan_unknown_barcode(client, admin_user, location):
    """Test step 2: Scanning unknown barcode shows new item form"""
    client.force_login(admin_user)

    # First select location
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "select_location", "location_id": location.id},
    )

    # Then scan unknown barcode
    new_barcode = "999888777666"
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "scan_barcode", "barcode": new_barcode},
    )

    assert response.status_code == 200
    assert "form_type" in response.context
    assert response.context["form_type"] == "new_item_form"
    assert response.context["barcode"] == new_barcode
    assert response.context["selected_location"] == location


def test_enrollment_step_3_add_new_item_valid(client, admin_user, location):
    """Test step 3: Adding valid new item information shows quantity form"""
    client.force_login(admin_user)

    # Setup: select location and scan barcode
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "select_location", "location_id": location.id},
    )

    new_barcode = "999888777666"
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "scan_barcode", "barcode": new_barcode},
    )

    # Add new item (must include barcode for form validation)
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {
            "action": "add_new_item",
            "name": "New Test Item",
            "manufacturer": "Test Manufacturer",
            "barcode": new_barcode,  # Required for form validation
        },
    )

    assert response.status_code == 200
    assert "form_type" in response.context
    assert response.context["form_type"] == "quantity_form"

    # Check that product was created
    assert Product.objects.filter(name="New Test Item", barcode=new_barcode).exists()


def test_enrollment_step_3_add_new_item_invalid(client, admin_user, location):
    """Test step 3: Adding invalid new item information shows form with errors"""
    client.force_login(admin_user)

    # Setup: select location and scan barcode
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "select_location", "location_id": location.id},
    )

    new_barcode = "999888777666"
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "scan_barcode", "barcode": new_barcode},
    )

    # Try to add item with missing name
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {
            "action": "add_new_item",
            "name": "",  # Invalid: empty name
            "manufacturer": "Test Manufacturer",
            "barcode": new_barcode,  # Required for form validation
        },
    )

    assert response.status_code == 200
    assert "form_type" in response.context
    assert response.context["form_type"] == "new_item_form"
    assert not response.context["form"].is_valid()


def test_enrollment_step_4_add_quantity(client, admin_user, location):
    """Test step 4: Adding quantity completes enrollment and creates inventory"""
    client.force_login(admin_user)

    # Setup: complete steps 1-3
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "select_location", "location_id": location.id},
    )

    new_barcode = "999888777666"
    client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "scan_barcode", "barcode": new_barcode},
    )

    client.post(
        reverse("inventory:add_item_to_location"),
        {
            "action": "add_new_item",
            "name": "New Test Item",
            "manufacturer": "Test Manufacturer",
            "barcode": new_barcode,
        },
    )

    # Add quantity
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "add_quantity", "quantity": 5},
    )

    # Should show scan form after successful completion
    assert response.status_code == 200
    assert response.context["form_type"] == "scan_form"

    # Verify product and inventory were created
    product = Product.objects.get(name="New Test Item", barcode=new_barcode)
    assert product is not None

    inventory = Inventory.objects.get(product=product, location=location)
    assert inventory.quantity == 5


def test_enrollment_complete_workflow(client, admin_user, location):
    """Test the complete enrollment workflow from start to finish"""
    client.force_login(admin_user)

    new_barcode = "111222333444"

    # Step 1: Select location
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "select_location", "location_id": location.id},
    )
    assert response.status_code == 200

    # Step 2: Scan unknown barcode
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "scan_barcode", "barcode": new_barcode},
    )
    assert response.status_code == 200

    # Step 3: Add product info
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {
            "action": "add_new_item",
            "name": "Complete Test Item",
            "manufacturer": "Complete Manufacturer",
            "barcode": new_barcode,
        },
    )
    assert response.status_code == 200

    # Step 4: Add quantity
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {"action": "add_quantity", "quantity": 10},
    )
    assert response.status_code == 200
    assert response.context["form_type"] == "scan_form"

    # Final verification
    assert Product.objects.filter(
        name="Complete Test Item", barcode=new_barcode
    ).exists()
    product = Product.objects.get(name="Complete Test Item", barcode=new_barcode)
    assert Inventory.objects.filter(
        product=product, location=location, quantity=10
    ).exists()


def test_enrollment_session_handling(client, admin_user, location):
    """Test that enrollment handles missing session data gracefully"""
    client.force_login(admin_user)

    # Try to skip to step 3 without proper session setup
    response = client.post(
        reverse("inventory:add_item_to_location"),
        {
            "action": "add_new_item",
            "name": "Test Item",
            "manufacturer": "Test Manufacturer",
        },
    )

    # Should redirect back to start due to missing session data
    assert response.status_code == 302
    assert response.url == reverse("inventory:add_item_to_location")
