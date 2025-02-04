from django import forms
from .models import BaseItem, Location, Inventory


class BaseItemForm(forms.ModelForm):
    class Meta:
        model = BaseItem
        fields = ["name", "variant", "barcode"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter item name"}
            ),
            "variant": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter item variant"}
            ),
            "barcode": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter barcode"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        variant = cleaned_data.get("variant")

        if name and variant:
            try:
                # Check for inactive item with same name/variant
                inactive_item = BaseItem.objects.get(
                    name=name, variant=variant, active=False
                )
                # If found, reactivate it
                inactive_item.activate()
                raise forms.ValidationError(
                    "This item was previously deactivated and has been restored.",
                    code="reactivated",
                )
            except BaseItem.DoesNotExist:
                # Check if active item with same name/variant exists
                if BaseItem.objects.filter(
                    name=name, variant=variant, active=True
                ).exists():
                    raise forms.ValidationError(
                        "An item with this name and variant already exists.",
                        code="exists",
                    )
        return cleaned_data


class LocationForm(forms.ModelForm):
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
        fields = ["base_item", "location", "quantity"]

    def clean(self):
        cleaned_data = super().clean()
        base_item = cleaned_data.get("base_item")
        location = cleaned_data.get("location")
        quantity = cleaned_data.get("quantity")

        if not all([base_item, location, quantity is not None]):
            return cleaned_data

        try:
            # First check for inactive item
            inactive_item = Inventory.objects.get(
                base_item=base_item, location=location, active=False
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
                    base_item=base_item, location=location, active=True
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
    base_item = forms.ModelChoiceField(queryset=BaseItem.objects.filter(active=True))
    location = forms.ModelChoiceField(queryset=Location.objects.filter(active=True))
    quantity = forms.IntegerField(min_value=1)


class EditInventoryForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=0)

    class Meta:
        model = Inventory
        fields = ["base_item", "location", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["base_item"].queryset = BaseItem.objects.filter(active=True)
        self.fields["location"].queryset = Location.objects.filter(active=True)


class StockUpdateForm(forms.Form):
    item_id = forms.IntegerField()
    delta_qty = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        item_id = cleaned_data.get("item_id")
        delta_qty = cleaned_data.get("delta_qty")

        if item_id and delta_qty is not None:
            try:
                inventory_item = Inventory.objects.get(id=item_id, active=True)

                # Prevent adding quantity if product is inactive
                if delta_qty > 0 and not inventory_item.base_item.active:
                    raise forms.ValidationError(
                        "Cannot add quantity to items with inactive products."
                    )

                # Check if reducing quantity would go below 0
                if inventory_item.quantity + delta_qty < 0:
                    raise forms.ValidationError("Cannot reduce quantity below 0")

            except Inventory.DoesNotExist:
                raise forms.ValidationError("Invalid inventory item")

        return cleaned_data


class RemoveLocationForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(active=True),
        empty_label="Select a location to remove",
        widget=forms.Select(attrs={"class": "form-control", "autofocus": True}),
    )


class RemoveBaseItemForm(forms.Form):
    base_item = forms.ModelChoiceField(
        queryset=BaseItem.objects.filter(active=True).order_by("name", "variant"),
        empty_label="Select an item to remove",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class AddItemToLocation(forms.Form):
    barcode = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Scan barcode",
                "autofocus": True,
            }
        ),
        label="Barcode",
    )


class NewBaseItemForm(BaseItemForm):
    class Meta(BaseItemForm.Meta):
        fields = ["name", "variant"]  # barcode will be set from scan


class AddQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter quantity",
                "autofocus": True,
            }
        ),
        min_value=1,
        label="Quantity to Add",
    )

    def __init__(self, *args, base_item=None, location=None, **kwargs):
        self.base_item = base_item
        self.location = location
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")

        if all([self.base_item, self.location, quantity]):
            try:
                # First check for inactive item
                inactive_item = Inventory.objects.get(
                    base_item=self.base_item, location=self.location, active=False
                )
                # Will reactivate in view
                cleaned_data["reactivate_item"] = inactive_item
            except Inventory.DoesNotExist:
                pass

            # Prevent adding quantity if product is inactive
            if not self.base_item.active:
                raise forms.ValidationError(
                    "Cannot add quantity to items with inactive products."
                )

        return cleaned_data


class ReactivateBaseItemForm(forms.Form):
    base_item = forms.ModelChoiceField(
        queryset=BaseItem.objects.filter(active=False).order_by("name", "variant"),
        empty_label="Select an item to reactivate",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class ReactivateLocationForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(active=False).order_by("name"),
        empty_label="Select a location to reactivate",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
