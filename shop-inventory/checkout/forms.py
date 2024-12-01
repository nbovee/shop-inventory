from django import forms
from django.db import transaction
from inventory.models import Inventory
from .models import Order, OrderItem
from django.utils import timezone
import uuid


class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(required=False)
    quantity = forms.IntegerField(min_value=1, required=False)
    barcode = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop("cart", {})
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        barcode = cleaned_data.get("barcode")
        product_id = cleaned_data.get("product_id")
        quantity = cleaned_data.get("quantity", 1)

        if not barcode and not product_id:
            raise forms.ValidationError("Either barcode or product ID must be provided")

        try:
            if barcode:
                self.inventory_item = Inventory.objects.get(base_item__barcode=barcode)
                cleaned_data["product_id"] = self.inventory_item.id
                cleaned_data["quantity"] = 1
            else:
                self.inventory_item = Inventory.objects.get(id=product_id)
                cleaned_data["quantity"] = quantity

            # Check if adding this quantity would exceed available stock
            cart_quantity = int(self.cart.get(str(self.inventory_item.id), 0))
            if self.inventory_item.quantity < cart_quantity + cleaned_data["quantity"]:
                raise forms.ValidationError(
                    f"Insufficient quantity in inventory for {self.inventory_item.base_item.name}"
                )

        except Inventory.DoesNotExist:
            raise forms.ValidationError("Product not found")

        return cleaned_data

    def save(self):
        """Update the cart with the new item."""
        product_id = str(self.cleaned_data["product_id"])
        quantity = self.cleaned_data["quantity"]

        if product_id in self.cart:
            self.cart[product_id] += quantity
        else:
            self.cart[product_id] = quantity

        return self.cart


class ProcessOrderForm(forms.Form):
    implicit_id = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your ID"}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop("cart", {})
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.cart:
            raise forms.ValidationError("Cart is empty")
        return cleaned_data

    def save(self):
        with transaction.atomic():
            # Generate a unique order number
            order_number = str(uuid.uuid4().hex[:8])

            # Create the order
            order = Order.objects.create(
                order_number=order_number,
                implicit_id=self.cleaned_data["implicit_id"],
                date=timezone.now(),
            )

            # Process each item in the cart
            for product_id, quantity in self.cart.items():
                try:
                    inventory_item = Inventory.objects.select_for_update().get(
                        id=product_id
                    )

                    # Check if we have enough stock
                    if inventory_item.quantity < quantity:
                        raise forms.ValidationError(
                            f"Insufficient stock for {inventory_item.base_item.name}"
                        )

                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        inventory_item=inventory_item,
                        quantity=quantity,
                        price_at_time=inventory_item.price,
                    )

                    # Update inventory
                    inventory_item.quantity -= quantity
                    inventory_item.save()

                except Inventory.DoesNotExist:
                    raise forms.ValidationError(
                        f"Product {product_id} no longer exists"
                    )

            return order
