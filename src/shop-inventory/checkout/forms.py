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
                # Inventory doesn't have a barcode field - need to look up via Product
                from inventory.models import normalize_barcode

                self.inventory_item = Inventory.objects.filter(
                    product__normalized_barcode=normalize_barcode(barcode)
                ).first()
                if not self.inventory_item:
                    raise Inventory.DoesNotExist("No inventory found for barcode")
                cleaned_data["product_id"] = self.inventory_item.id
                cleaned_data["quantity"] = 1
            else:
                self.inventory_item = Inventory.objects.get(id=product_id)
                cleaned_data["quantity"] = quantity

            # Check if adding this quantity would exceed available stock
            cart_quantity = int(self.cart.get(str(self.inventory_item.id), 0))
            if self.inventory_item.quantity < cart_quantity + cleaned_data["quantity"]:
                raise forms.ValidationError(
                    f"Insufficient quantity in inventory for {self.inventory_item.product.name}"
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


class ProcessOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["implicit_id"]
        widgets = {
            "implicit_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your Rowan email or ID",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop("cart", {})
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.cart:
            raise forms.ValidationError("Cart is empty")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.order_number = str(uuid.uuid4().hex[:8])
        instance.date = timezone.now()

        if commit:
            with transaction.atomic():
                instance.save()

                # Process each item in the cart
                for product_id, quantity in self.cart.items():
                    try:
                        inventory_item = Inventory.objects.select_for_update().get(
                            id=product_id
                        )

                        # Check if we have enough stock
                        if inventory_item.quantity < quantity:
                            raise forms.ValidationError(
                                f"Insufficient stock for {inventory_item.product.name}"
                            )

                        # Create order item
                        OrderItem.objects.create(
                            order=instance,
                            inventory_item=inventory_item,
                            quantity=quantity,
                        )

                        # Update inventory
                        inventory_item.quantity -= quantity
                        inventory_item.save()

                    except Inventory.DoesNotExist:
                        raise forms.ValidationError(
                            f"Product {product_id} no longer exists"
                        )

        return instance
