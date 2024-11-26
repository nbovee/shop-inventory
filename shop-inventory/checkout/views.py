from django.shortcuts import render, redirect
from django.contrib import messages
from inventory.models import Inventory
from .forms import AddToCartForm


def index(request):
    return render(request, "checkout/index.html")


def get_cart(request):
    """Retrieve the cart from the session."""
    return request.session.get("cart", {})


def add_to_cart(request):
    """Add an item to the cart stored in the session."""
    if request.method == "POST":
        form = AddToCartForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data["product_id"]
            quantity = form.cleaned_data["quantity"]

            # Validate that the product exists in the inventory
            if not Inventory.objects.filter(id=product_id).exists():
                messages.error(
                    request, "The selected product does not exist in inventory."
                )
                return redirect("cart")

            # Retrieve the current cart
            cart = get_cart(request)

            # Update the cart with the new item or quantity
            if product_id in cart:
                cart[product_id] += quantity
            else:
                cart[product_id] = quantity

            # Save the updated cart back to the session
            request.session["cart"] = cart
            messages.success(request, "Item added to cart.")
            return redirect("cart")
    else:
        form = AddToCartForm()

    return render(request, "checkout/cart.html", {"form": form})


def view_cart(request):
    """Display the cart."""
    cart = get_cart(request)
    return render(request, "checkout/cart.html", {"cart": cart})


def process_order(request):
    """Process the order based on the cart in the session."""
    cart = get_cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("index")

    # Here you would handle the order processing logic
    # For example, creating an Order object and saving it to the database

    # Clear the cart after processing
    del request.session["cart"]
    messages.success(request, "Order processed successfully.")
    return redirect("order_confirmation")
