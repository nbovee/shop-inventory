from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required, permission_required
from inventory.models import Inventory, normalize_barcode
from .models import Order
from .forms import AddToCartForm, ProcessOrderForm


def index(request):
    if request.method == "POST":
        # Handle barcode scanning
        barcode = request.POST.get("barcode")
        if barcode:
            try:
                # Find the inventory item with matching barcode
                inventory_item = Inventory.objects.filter(
                    product__normalized_barcode=normalize_barcode(barcode),
                    location__name__icontains="Shopfloor",
                    quantity__gt=0,
                ).first()

                if inventory_item:
                    # Prepare data for the form
                    form_data = {
                        "product_id": str(inventory_item.id),
                        "quantity": request.POST.get("quantity", 1),
                    }
                    form = AddToCartForm(form_data, cart=get_cart(request))
                    if form.is_valid():
                        request.session["cart"] = form.save()
                        messages.success(
                            request, f"Added {inventory_item.product.name} to cart."
                        )
                    else:
                        for error in form.non_field_errors():
                            messages.error(request, error)
                else:
                    messages.error(request, f"No item found with barcode: {barcode}")
                return redirect("checkout:index")
            except Exception as e:
                messages.error(request, f"Error processing barcode: {str(e)}")
                return redirect("checkout:index")

        # Handle normal add to cart (from product list)
        form = AddToCartForm(request.POST, cart=get_cart(request))
        if form.is_valid():
            try:
                # Update cart in session
                request.session["cart"] = form.save()
                messages.success(request, "Item added to cart.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
        return redirect("checkout:index")

    # Handle GET request
    filter_term = request.GET.get("filter", "")
    inventory_items = Inventory.objects.filter(
        (
            models.Q(product__name__icontains=filter_term)
            | models.Q(product__manufacturer__icontains=filter_term)
        )
        & models.Q(location__name__icontains="Shopfloor")
        & models.Q(quantity__gt=0)
    )
    return render(request, "checkout/index.html", {"inventory_items": inventory_items})


def get_cart(request):
    """Retrieve the cart from the session."""
    return request.session.get("cart", {})


def remove_from_cart(request):
    """Remove an item from the cart."""
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        if product_id:
            # Get the current cart
            cart = get_cart(request)

            # Remove the item if it exists in the cart
            if product_id in cart:
                del cart[product_id]
                request.session["cart"] = cart
                messages.success(request, "Item removed from cart.")
            else:
                messages.error(request, "Item not found in cart.")

    return redirect("checkout:index")


def process_order(request):
    """Process the order based on the cart in the session."""
    cart = get_cart(request)

    if request.method == "POST":
        form = ProcessOrderForm(request.POST, cart=cart, request=request)
        if form.is_valid():
            try:
                order = form.save()
                # Clear the cart after successful order
                del request.session["cart"]
                messages.success(
                    request,
                    f"Order #{order.order_number} processed successfully for user {order.implicit_id}",
                )
                return redirect("index")
            except Exception as e:
                messages.error(request, str(e))
        else:
            for error in form.errors.values():
                messages.error(request, error)
            for error in form.non_field_errors():
                messages.error(request, error)

    return redirect("index")


@login_required
@permission_required("checkout.view_order", raise_exception=True)
def recent_orders(request):
    """Display orders from the last 30 days."""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = (
        Order.objects.filter(date__gte=thirty_days_ago)
        .order_by("-date")
        .prefetch_related(
            "items", "items__inventory_item", "items__inventory_item__product"
        )
    )

    return render(
        request, "checkout/recent_orders.html", {"recent_orders": recent_orders}
    )
