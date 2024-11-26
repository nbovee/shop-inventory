from django import forms
from .models import BaseItem, Location, Inventory


class BaseItemForm(forms.ModelForm):
    class Meta:
        model = BaseItem
        fields = ["name", "variant"]


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["name"]


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ["base_item", "location", "quantity", "barcode"]

    def clean(self):
        cleaned_data = super().clean()
        base_item = cleaned_data.get("base_item")
        location = cleaned_data.get("location")
        quantity = cleaned_data.get("quantity")

        if base_item and location:
            try:
                existing_item = Inventory.objects.get(
                    base_item=base_item, location=location
                )
                cleaned_data["quantity"] = existing_item.quantity + quantity
            except Inventory.DoesNotExist:
                pass
        return cleaned_data


class RemoveInventoryForm(forms.Form):
    base_item = forms.ModelChoiceField(queryset=BaseItem.objects.all())
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    quantity = forms.IntegerField(min_value=1)


class EditInventoryForm(forms.ModelForm):
    barcode = forms.UUIDField()
    quantity = forms.IntegerField(min_value=0)

    class Meta:
        model = Inventory
        fields = ["base_item", "location", "barcode", "quantity"]


class StockUpdateForm(forms.Form):
    item_id = forms.IntegerField()
    delta_qty = forms.IntegerField()
