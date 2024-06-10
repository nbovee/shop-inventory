# inventory_app/inventory/forms.py

from django import forms
from .models import BaseItem, Location, Inventory

class BaseItemForm(forms.ModelForm):
    class Meta:
        model = BaseItem
        fields = ['name', 'barcode_number', 'active']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'barcode_number', 'active']

class InventoryForm(forms.Form):
    base_item_name = forms.CharField(max_length=30)
    location_name = forms.CharField(max_length=30)
    quantity = forms.IntegerField(min_value=1)

class RemoveInventoryForm(forms.Form):
    base_item_name = forms.CharField(max_length=30)
    location_name = forms.CharField(max_length=30)
    quantity = forms.IntegerField(min_value=1)

