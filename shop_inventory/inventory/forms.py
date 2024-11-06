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
