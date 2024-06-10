# inventory_app/inventory/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import BaseItem, Location, Inventory
from .forms import InventoryForm, RemoveInventoryForm

def index(request):
    inventory_items = Inventory.objects.all()
    return render(request, 'inventory/index.html', {'inventory_items': inventory_items})

def add_inventory(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            base_item_name = form.cleaned_data['base_item_name']
            location_name = form.cleaned_data['location_name']
            quantity = form.cleaned_data['quantity']

            base_item, _ = BaseItem.objects.get_or_create(name=base_item_name)
            location, _ = Location.objects.get_or_create(name=location_name)

            inventory_item, created = Inventory.objects.get_or_create(
                base_item=base_item,
                location=location,
                defaults={'quantity': quantity}
            )
            if not created:
                inventory_item.quantity += quantity
                inventory_item.save()
            messages.success(request, 'Inventory item added/updated successfully.')
            return redirect('index')
    else:
        form = InventoryForm()
    return render(request, 'inventory/add_item.html', {'form': form})

def remove_inventory(request):
    if request.method == 'POST':
        form = RemoveInventoryForm(request.POST)
        if form.is_valid():
            base_item_name = form.cleaned_data['base_item_name']
            location_name = form.cleaned_data['location_name']
            quantity = form.cleaned_data['quantity']

            try:
                base_item = BaseItem.objects.get(name=base_item_name)
                location = Location.objects.get(name=location_name)
                inventory_item = Inventory.objects.get(base_item=base_item, location=location)
                if inventory_item.quantity >= quantity:
                    inventory_item.quantity -= quantity
                    if inventory_item.quantity == 0:
                        inventory_item.delete()
                    else:
                        inventory_item.save()
                    messages.success(request, 'Inventory item removed successfully.')
                else:
                    messages.error(request, 'Not enough quantity to remove.')
            except (BaseItem.DoesNotExist, Location.DoesNotExist, Inventory.DoesNotExist):
                messages.error(request, 'Inventory item not found.')
            return redirect('index')
    else:
        form = RemoveInventoryForm()
    return render(request, 'inventory/remove_item.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'inventory/login.html')

