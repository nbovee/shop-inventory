from django import forms
from .models import Inventory,BaseItem, Location


class BaseItemForm(forms.ModelForm):
    class Meta:
        model = BaseItem
        fields = ["name", "barcode_number"]

class InventoryForm(forms.ModelForm):
    location = forms.ModelChoiceField(queryset=Location.objects.all(), empty_label="(Choose One)", label="Location")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].label_from_instance = self.label_from_location_instance

    def label_from_location_instance(self, obj):
        return obj.name
    
    class Meta:
        model = Inventory
        fields = ["quantity", "location", "notes"]

class LocationForm(forms.ModelForm):
    
    class Meta:
        model =Location
        fields = ["name", "barcode_number"]
