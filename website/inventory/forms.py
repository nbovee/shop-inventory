# inventory_app/inventory/forms.py
from django import forms
from .models import Item

class AddItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'quantity']

class RemoveItemForm(forms.Form):
    name = forms.CharField(max_length=200)
    quantity = forms.IntegerField(min_value=1)
