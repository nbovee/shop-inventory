from django import forms
from .models import CartItem, Cart, Order


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ["quantity", "product"]


class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ["items"]


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["implicit_id"]
        error_messages = {
            "implicit_id": {
                "invalid": "Please enter either your Rowan email address or scan your RowanCard.",
            },
        }
