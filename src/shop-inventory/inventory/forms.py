from django import forms
from .models import Product, Location, Inventory, validate_barcode


class AddProductForm(forms.ModelForm):
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(active=True).order_by('name'),
        empty_label="Select a location",
        widget=forms.Select(attrs={"class": "form-control"}),
        required=True
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "value": "1"}),
        initial=1,
        required=True
    )
    barcode = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Product
        fields = ["name", "manufacturer", "barcode", "location", "quantity"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter item name"}
            ),
            "manufacturer": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter manufacturer"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        manufacturer = cleaned_data.get("manufacturer")

        if name and manufacturer:
            try:
                # Check for inactive item with same name/manufacturer
                inactive_item = Product.objects.get(
                    name=name, manufacturer=manufacturer, active=False
                )
                # If found, reactivate it
                inactive_item.activate()
                raise forms.ValidationError(
                    "This item was previously deactivated and has been restored.",
                    code="reactivated",
                )
            except Product.DoesNotExist:
                # Check if active item with same name/manufacturer exists
                if Product.objects.filter(
                    name=name, manufacturer=manufacturer, active=True
                ).exists():
                    raise forms.ValidationError(
                        "An item with this name and manufacturer already exists.",
                        code="exists",
                    )
        return cleaned_data


class AddLocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter location name"}
            )
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        try:
            # Check for inactive location with same name
            inactive_location = Location.objects.get(name=name, active=False)
            # If found, reactivate it
            inactive_location.active = True
            inactive_location.save()
            raise forms.ValidationError(
                "This location was previously deactivated and has been restored.",
                code="reactivated",
            )
        except Location.DoesNotExist:
            # Check if active location with same name exists
            if Location.objects.filter(name=name, active=True).exists():
                raise forms.ValidationError(
                    "A location with this name already exists.", code="exists"
                )
        return name


class AddInventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ["product", "location", "quantity"]

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        location = cleaned_data.get("location")
        quantity = cleaned_data.get("quantity")

        if not all([product, location, quantity is not None]):
            return cleaned_data

        try:
            # First check for inactive item
            inactive_item = Inventory.objects.get(
                product=product, location=location, active=False
            )
            # Reactivate the item and update its quantity
            inactive_item.quantity = quantity
            inactive_item.activate()
            raise forms.ValidationError(
                "This inventory item was previously deactivated and has been restored.",
                code="reactivated",
            )
        except Inventory.DoesNotExist:
            # Then check for active item
            try:
                existing_item = Inventory.objects.get(
                    product=product, location=location, active=True
                )
                # Update existing item's quantity and barcode
                existing_item.quantity += quantity
                existing_item.save()
                raise forms.ValidationError(
                    f"Updated existing inventory item. New quantity: {existing_item.quantity}",
                    code="updated",
                )
            except Inventory.DoesNotExist:
                # Will create new item during form.save()
                pass

        return cleaned_data


class RemoveInventoryForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(active=True))
    location = forms.ModelChoiceField(queryset=Location.objects.filter(active=True))
    quantity = forms.IntegerField(min_value=1)


class InventoryQuantityUpdateForm(forms.Form):
    item_id = forms.IntegerField()
    delta_qty = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        location = cleaned_data.get("location")
        delta_qty = cleaned_data.get("delta_qty")

        if all([product, location, delta_qty is not None]):
            try:
                inventory_item = Inventory.objects.get(
                    product=product, location=location, active=True
                )

                # Prevent adding quantity if product is inactive
                if delta_qty > 0 and not inventory_item.product.active:
                    raise forms.ValidationError(
                        "Cannot add quantity to items with inactive products."
                    )

                # Check if reducing quantity would go below 0
                if inventory_item.quantity + delta_qty < 0:
                    raise forms.ValidationError("Cannot reduce quantity below 0")

            except Inventory.DoesNotExist:
                raise forms.ValidationError(
                    "No active inventory found for this product and location combination."
                )

        return cleaned_data


class DeactivateLocationForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(active=True),
        empty_label="Select a location to remove",
        widget=forms.Select(attrs={"class": "form-control", "autofocus": True}),
    )


class DeactivateProductForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(active=True).order_by("name", "manufacturer"),
        empty_label="Select a product to remove",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class BarcodeForm(forms.Form):
    barcode = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Scan barcode",
                "autofocus": True,
            }
        ),
        label="Barcode",
        validators=[validate_barcode],
    )


class AddItemToLocationForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(active=True).order_by("name"),
        empty_label="Select a location to add item",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class AddQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter quantity",
                "autofocus": True,
            }
        ),
        label="Quantity",
    )


class NewProductForm(AddProductForm):
    class Meta(AddProductForm.Meta):
        fields = ["name", "manufacturer"]  # barcode will be set from scan


class ReactivateProductForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(active=False).order_by("name", "manufacturer"),
        empty_label="Select an item to reactivate",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def save(self):
        product = self.cleaned_data["product"]
        product.activate()  # Using the model's activate method
        return product


class ReactivateLocationForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(active=False).order_by("name"),
        empty_label="Select a location to reactivate",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "manufacturer"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter item name"}
            ),
            "manufacturer": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter manufacturer"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.pop("instance_id", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        manufacturer = cleaned_data.get("manufacturer")

        if name and manufacturer:
            # Check if another product with same name/manufacturer exists (excluding this one)
            duplicate_exists = (
                Product.objects.filter(
                    name=name, manufacturer=manufacturer, active=True
                )
                .exclude(id=self.instance.id)
                .exists()
            )

            if duplicate_exists:
                raise forms.ValidationError(
                    "Another item with this name and manufacturer already exists.",
                    code="exists",
                )
        return cleaned_data


class SelectProductForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(active=True).order_by("name", "manufacturer"),
        empty_label="Select a product to edit",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
