from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cart
from .forms import CartItemForm, CartForm


# Create your views here.
def get_or_create_cart(request):
    """Helper function to get or create a cart based on session"""
    if not request.session.session_key:
        request.session.create()

    cart = Cart.objects.filter(session_key=request.session.session_key).first()
    if not cart:
        cart = Cart.objects.create(session_key=request.session.session_key)
    return cart


def index(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()

    if request.method == "POST":
        if "add_cartitem" in request.POST:
            form = CartItemForm(request.POST)
            if form.is_valid():
                cart_item = form.save(commit=False)
                cart_item.cart = cart
                cart_item.save()
                messages.success(request, "Item added to cart.")
        elif "enter_implicit_id" in request.POST:
            form = CartForm(request.POST, instance=cart)
            if form.is_valid():
                form.save()
                messages.success(request, "ID added successfully.")
        elif "process_cart" in request.POST:
            if not cart.implicit_id:
                messages.error(request, "Please enter your Rowan ID or email first.")
            else:
                return redirect("process_order")
        return redirect("cart")
    else:
        forms = [CartItemForm(instance=item) for item in cart_items]
    return render(request, "checkout.html", {"cart_items": zip(cart_items, forms)})


def process_order(request):
    cart = get_or_create_cart(request)
    if not cart.implicit_id:
        messages.error(request, "Please enter your Rowan ID or email first.")
        return redirect("cart")

    cart.process_order()
    # Clear the cart's session key after processing
    cart.session_key = None
    cart.save()
    messages.success(request, "Order processed successfully.")
    return redirect("order_confirmation")
