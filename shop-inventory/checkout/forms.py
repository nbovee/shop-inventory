from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["implicit_id"]
        error_messages = {
            "implicit_id": {
                "invalid": "Please enter either your Rowan email address or scan your RowanCard.",
            },
        }


class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(label="Product ID", min_value=1)
    quantity = forms.IntegerField(label="Quantity", min_value=1, initial=1)
