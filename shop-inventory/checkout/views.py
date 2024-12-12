from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required, permission_required
from inventory.models import Inventory
from .models import Order
from .forms import AddToCartForm, ProcessOrderForm


def index(request):
    if request.method == "POST":
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
            models.Q(base_item__name__icontains=filter_term)
            | models.Q(base_item__variant__icontains=filter_term)
        )
        & models.Q(location__name__icontains="Floor")
        & models.Q(quantity__gt=0)
    )
    return render(request, "checkout/index.html", {"inventory_items": inventory_items})


def get_cart(request):
    """Retrieve the cart from the session."""
    return request.session.get("cart", {})


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
@permission_required("inventory.add_baseitem", raise_exception=True)
def recent_orders(request):
    """Display orders from the last 30 days."""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = (
        Order.objects.filter(date__gte=thirty_days_ago)
        .order_by("-date")
        .prefetch_related(
            "items", "items__inventory_item", "items__inventory_item__base_item"
        )
    )

    return render(
        request, "checkout/recent_orders.html", {"recent_orders": recent_orders}
    )
