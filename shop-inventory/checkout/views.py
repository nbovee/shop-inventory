from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from inventory.models import Inventory
from .forms import AddToCartForm


def index(request):
    if request.method == "POST":
        if "barcode" in request.POST:
            barcode = request.POST.get("barcode")
            try:
                inventory_item = Inventory.objects.get(base_item__barcode=barcode)
                product_id = inventory_item.id
                quantity = 1
            except Inventory.DoesNotExist:
                messages.error(request, "Product with this barcode not found.")
                return redirect("checkout")
        else:
            form = AddToCartForm(request.POST)
            if not form.is_valid():
                messages.error(request, "Invalid form submission.")
                return redirect("checkout")
            product_id = form.cleaned_data["product_id"]
            quantity = form.cleaned_data["quantity"]

        # Validate that the product exists in the inventory
        if not Inventory.objects.filter(id=product_id).exists():
            messages.error(request, "The selected product does not exist in inventory.")
            return redirect("checkout")

        # Retrieve the current cart
        cart = get_cart(request)

        # Update the cart with the new item or quantity
        if str(product_id) in cart:
            inventory_item = Inventory.objects.get(id=product_id)
            if inventory_item.quantity >= cart[str(product_id)] + quantity:
                cart[str(product_id)] += quantity
            else:
                messages.error(request, "Insufficient quantity in inventory.")
                return redirect("checkout")
        else:
            cart[str(product_id)] = quantity

        # Save the updated cart back to the session
        request.session["cart"] = cart
        messages.success(request, "Item added to cart.")
        return redirect("checkout")

    # Handle GET request
    filter_term = request.GET.get("filter", "")
    inventory_items = Inventory.objects.filter(
        models.Q(base_item__name__icontains=filter_term)
        | models.Q(base_item__variant__icontains=filter_term)
    )
    return render(request, "checkout/index.html", {"inventory_items": inventory_items})


def get_cart(request):
    """Retrieve the cart from the session."""
    return request.session.get("cart", {})


def view_cart(request):
    """Display the cart."""
    cart = get_cart(request)
    return render(request, "checkout/cart.html", {"cart": cart})


def process_order(request):
    """Process the order based on the cart in the session."""
    cart = get_cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("checkout")

    # Here you would handle the order processing logic
    # For example, creating an Order object and saving it to the database

    # Clear the cart after processing
    del request.session["cart"]
    messages.success(request, "Order processed successfully.")
    return redirect("checkout")
