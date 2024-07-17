from django import forms
from .models import BaseItem, Location, Inventory

class BaseItemForm(forms.ModelForm):
    class Meta:
        model = BaseItem
        fields = ['name', 'barcode_number']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name']

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['base_item', 'location', 'quantity']

class RemoveInventoryForm(forms.Form):
    base_item = forms.ModelChoiceField(queryset=BaseItem.objects.all())
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    quantity = forms.IntegerField(min_value=1)

class EditInventoryForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=0)
    
    class Meta:
        model = Inventory
        fields = ['base_item', 'location', 'quantity']

