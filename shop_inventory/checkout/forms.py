from django import forms
from inventory.models import Inventory,BaseItem,Location

class checkoutForm(forms.Form):
    quantity_JSON = forms.Select()