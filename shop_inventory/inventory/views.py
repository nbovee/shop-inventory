# from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, View, DeleteView
from .models import Inventory
from django.shortcuts import render, redirect
from .forms import BaseItemForm, InventoryForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .forms import InventoryForm

class Index(TemplateView):
    template_name = "inventory/index.html"

class InventoryList(View):
    def get(self, request):
        items = Inventory.objects.all()
        return render(request, "inventory/inventorylist.html", {"items": items})
    
class AddInventory(View):
     def get(self, request):
        base_item_form = BaseItemForm()
        inventory_form = InventoryForm()
        return render(request, "inventory/add_inventory.html", {
            "base_item_form": base_item_form,
            "inventory_form": inventory_form
        })
     def post(self, request):
        base_item_form = BaseItemForm(request.POST)
        inventory_form = InventoryForm(request.POST)
        
        if base_item_form.is_valid() and inventory_form.is_valid():
            base_item = base_item_form.save()
            inventory = inventory_form.save(commit=False)
            inventory.base_item = base_item
            inventory.save()
            return redirect("inventory:InventoryList")  # Redirect to the inventory list view after saving
        
        return render(request, "inventory/add_inventory.html", {
            "base_item_form": base_item_form,
            "inventory_form": inventory_form
        })


class DeleteInventory(DeleteView):    
    model = Inventory
    template_name = "inventory/delete_inventory.html"
    context_object_name = "item"
    success_url = reverse_lazy("inventory:InventoryList")

class EditInventory(View):
    template_name = 'inventory/update_inventory.html'

    def get_object(self):
        # Assuming the URL contains the ID of the inventory item to be updated
        inventory_id = self.kwargs.get('pk')
        return get_object_or_404(Inventory, pk=inventory_id)

    def get(self, request, *args, **kwargs):
        inventory = self.get_object()
        base_item_form = BaseItemForm(instance=inventory.base_item)
        inventory_form = InventoryForm(instance=inventory)
        return render(request, self.template_name, {
            'base_item_form': base_item_form,
            'inventory_form': inventory_form,
        })
    def post(self, request, *args, **kwargs):
        inventory = self.get_object()
        base_item_form = BaseItemForm(request.POST, instance=inventory.base_item)
        inventory_form = InventoryForm(request.POST, instance=inventory)

        if base_item_form.is_valid() and inventory_form.is_valid():
            base_item_form.save()
            inventory_form.save()
            return redirect('inventory:InventoryList')  # Adjust the redirect as needed

        return render(request, self.template_name, {
            'base_item_form': base_item_form,
            'inventory_form': inventory_form,
        })

   
   