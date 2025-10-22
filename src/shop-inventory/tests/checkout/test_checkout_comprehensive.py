"""
Comprehensive checkout tests that verify complete user workflows.

These tests verify the end-to-end checkout process including cart management,
barcode scanning, UPC-A type 2 normalization, and order processing.
"""

import pytest
from django.urls import reverse
from inventory.models import Product, Location, Inventory
from checkout.models import Order, OrderItem


pytestmark = pytest.mark.django_db


def test_checkout_complete_workflow(client, shopfloor):
    """
    Test the complete checkout workflow from scanning to order completion.

    This verifies:
    - Barcode scanning adds items to cart
    - Scanning same barcode increases quantity
    - Scanning different barcode adds separate item
    - Order processing creates Order and OrderItems
    - Inventory is decremented correctly
    - Cart is cleared after successful order
    """
    # Setup: Create products and inventory

    product1 = Product.objects.create(
        name="Test Item 1",
        manufacturer="Brand A",
        barcode="123456789012",
    )
    inventory1 = Inventory.objects.create(
        product=product1,
        location=shopfloor,
        quantity=10,
    )

    product2 = Product.objects.create(
        name="Test Item 2",
        manufacturer="Brand B",
        barcode="987654321098",
    )
    inventory2 = Inventory.objects.create(
        product=product2,
        location=shopfloor,
        quantity=15,
    )

    # Initialize empty cart in session
    session = client.session
    session["cart"] = {}
    session.save()

    url = reverse("checkout:index")

    # Step 1: Scan first barcode
    response = client.post(url, {"barcode": "123456789012", "quantity": 1})
    assert response.status_code == 302

    # Verify cart has item with quantity 1
    cart = client.session.get("cart", {})
    assert str(inventory1.id) in cart
    assert cart[str(inventory1.id)] == 1

    # Step 2: Scan same barcode again
    response = client.post(url, {"barcode": "123456789012", "quantity": 1})
    assert response.status_code == 302

    # Verify cart now has quantity 2
    cart = client.session.get("cart", {})
    assert cart[str(inventory1.id)] == 2

    # Step 3: Scan different barcode
    response = client.post(url, {"barcode": "987654321098", "quantity": 1})
    assert response.status_code == 302

    # Verify cart has 2 items
    cart = client.session.get("cart", {})
    assert len(cart) == 2
    assert str(inventory2.id) in cart
    assert cart[str(inventory2.id)] == 1

    # Step 4: Process order
    process_url = reverse("checkout:process_order")
    response = client.post(process_url, {"implicit_id": "test@rowan.edu"})
    assert response.status_code == 302

    # Verify order was created
    assert Order.objects.filter(implicit_id="test@rowan.edu").exists()
    order = Order.objects.get(implicit_id="test@rowan.edu")

    # Verify OrderItems were created
    assert order.items.count() == 2

    order_item1 = OrderItem.objects.get(order=order, inventory_item=inventory1)
    assert order_item1.quantity == 2

    order_item2 = OrderItem.objects.get(order=order, inventory_item=inventory2)
    assert order_item2.quantity == 1

    # Verify inventory was decremented
    inventory1.refresh_from_db()
    inventory2.refresh_from_db()
    assert inventory1.quantity == 8  # 10 - 2
    assert inventory2.quantity == 14  # 15 - 1

    # Verify cart was cleared
    assert "cart" not in client.session


def test_checkout_upc_a_type_2_normalization(client, shopfloor):
    """
    Test that UPC-A type 2 barcodes normalize correctly in checkout.

    Variable weight items (number system 2) should normalize the weight/price
    portion to zeros, allowing different scans of the same item to be recognized
    as the same product in the cart.
    """
    # Setup: Create product with type 2 barcode

    product = Product.objects.create(
        name="Variable Weight Item",
        manufacturer="Fresh Foods",
        barcode="234567123456",  # Type 2 UPC-A
    )
    assert product.normalized_barcode == "234567000000"

    inventory = Inventory.objects.create(
        product=product,
        location=shopfloor,
        quantity=20,
    )

    # Initialize empty cart
    session = client.session
    session["cart"] = {}
    session.save()

    url = reverse("checkout:index")

    # Step 1: Scan first barcode (234567123456)
    response = client.post(url, {"barcode": "234567123456", "quantity": 1})
    assert response.status_code == 302

    cart = client.session.get("cart", {})
    assert str(inventory.id) in cart
    assert cart[str(inventory.id)] == 1

    # Step 2: Scan second barcode with different tail (234567654321)
    # This should recognize it as the SAME product due to normalization
    response = client.post(url, {"barcode": "234567654321", "quantity": 1})
    assert response.status_code == 302

    # Verify cart still has only 1 item, with quantity increased to 2
    cart = client.session.get("cart", {})
    assert len(cart) == 1
    assert str(inventory.id) in cart
    assert cart[str(inventory.id)] == 2

    # Step 3: Process order
    response = client.post(
        reverse("checkout:process_order"), {"implicit_id": "customer@rowan.edu"}
    )
    assert response.status_code == 302

    # Verify only 1 OrderItem created with quantity 2
    order = Order.objects.get(implicit_id="customer@rowan.edu")
    assert order.items.count() == 1

    order_item = order.items.first()
    assert order_item.inventory_item == inventory
    assert order_item.quantity == 2

    # Verify inventory decremented by 2
    inventory.refresh_from_db()
    assert inventory.quantity == 18


def test_checkout_multiple_items_single_order(client, shopfloor):
    """
    Test checkout with multiple different items in a single order.

    Verifies that multiple products can be added to cart and processed
    together, with all inventory updates happening correctly.
    """
    # Setup: Create 3 different products

    products = []
    inventories = []
    for i in range(3):
        product = Product.objects.create(
            name=f"Item {i+1}",
            manufacturer=f"Maker {i+1}",
            barcode=f"11122233344{i}",
        )
        inventory = Inventory.objects.create(
            product=product,
            location=shopfloor,
            quantity=10 + i * 5,  # 10, 15, 20
        )
        products.append(product)
        inventories.append(inventory)

    # Initialize cart
    session = client.session
    session["cart"] = {}
    session.save()

    url = reverse("checkout:index")

    # Scan all 3 barcodes with different quantities
    quantities = [2, 3, 1]
    for i, qty in enumerate(quantities):
        response = client.post(url, {"barcode": products[i].barcode, "quantity": 1})
        # Scan multiple times to reach desired quantity
        for _ in range(qty - 1):
            response = client.post(url, {"barcode": products[i].barcode, "quantity": 1})

    # Verify cart has 3 items
    cart = client.session.get("cart", {})
    assert len(cart) == 3
    for i, qty in enumerate(quantities):
        assert cart[str(inventories[i].id)] == qty

    # Process order
    response = client.post(
        reverse("checkout:process_order"), {"implicit_id": "multi@rowan.edu"}
    )
    assert response.status_code == 302

    # Verify order and order items
    order = Order.objects.get(implicit_id="multi@rowan.edu")
    assert order.items.count() == 3

    # Verify each inventory item decremented correctly
    for i, (inventory, qty) in enumerate(zip(inventories, quantities)):
        order_item = OrderItem.objects.get(order=order, inventory_item=inventory)
        assert order_item.quantity == qty

        inventory.refresh_from_db()
        expected_qty = (10 + i * 5) - qty
        assert inventory.quantity == expected_qty


def test_checkout_insufficient_stock_during_order(client, shopfloor):
    """
    Test checkout when inventory becomes insufficient between adding to cart and processing.

    This tests the edge case where an item is added to cart, but inventory
    is reduced (by another process) before order is processed.
    """
    # Setup

    product = Product.objects.create(
        name="Limited Stock Item",
        manufacturer="Rare Goods",
        barcode="555666777888",
    )
    inventory = Inventory.objects.create(
        product=product,
        location=shopfloor,
        quantity=10,
    )

    # Initialize cart and add 5 items
    session = client.session
    session["cart"] = {str(inventory.id): 5}
    session.save()

    # Simulate concurrent checkout reducing stock to 3
    inventory.quantity = 3
    inventory.save()

    # Attempt to process order (should fail - not enough stock)
    response = client.post(
        reverse("checkout:process_order"), {"implicit_id": "greedy@rowan.edu"}
    )
    assert response.status_code == 302

    # Verify order was NOT created
    assert not Order.objects.filter(implicit_id="greedy@rowan.edu").exists()

    # Verify cart still exists (order failed)
    cart = client.session.get("cart", {})
    assert str(inventory.id) in cart
    assert cart[str(inventory.id)] == 5

    # Verify inventory unchanged (order rolled back)
    inventory.refresh_from_db()
    assert inventory.quantity == 3
