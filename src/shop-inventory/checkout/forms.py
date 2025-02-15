from django import forms
from django.db import transaction
from inventory.models import InventoryEntry
from .models import Order, OrderItem
from django.utils import timezone
import uuid
from django.contrib import messages


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
                self.inventory_item = InventoryEntry.objects.get(barcode=barcode)
                cleaned_data["product_id"] = self.inventory_item.id
                cleaned_data["quantity"] = 1
            else:
                self.inventory_item = InventoryEntry.objects.get(id=product_id)
                cleaned_data["quantity"] = quantity

            # Check if adding this quantity would exceed available stock
            cart_quantity = int(self.cart.get(str(self.inventory_item.id), 0))
            if self.inventory_item.quantity < cart_quantity + cleaned_data["quantity"]:
                raise forms.ValidationError(
                    f"Insufficient quantity in inventory for {self.inventory_item.product.name}"
                )

        except InventoryEntry.DoesNotExist:
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
                deactivated_items = []

                # Process each item in the cart
                for product_id, quantity in self.cart.items():
                    try:
                        inventory_item = InventoryEntry.objects.select_for_update().get(
                            id=product_id, active=True
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

                        # Check if item should be deactivated
                        if (
                            inventory_item.quantity == 0
                            and not inventory_item.product.active
                        ):
                            inventory_item.active = False
                            deactivated_items.append(inventory_item.product.name)

                        inventory_item.save()

                    except InventoryEntry.DoesNotExist:
                        raise forms.ValidationError(
                            f"Product {product_id} no longer exists"
                        )

                # Add message about deactivated items if any
                if deactivated_items and self.request:
                    messages.info(
                        self.request,
                        f"The following items have been deactivated as they reached zero quantity: {', '.join(deactivated_items)}",
                    )

        return instance
