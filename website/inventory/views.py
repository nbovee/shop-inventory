# inventory_app/inventory/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Item
from .forms import AddItemForm, RemoveItemForm

def index(request):
    items = Item.objects.all()
    return render(request, 'inventory/index.html', {'items': items})

def add_item(request):
    if request.method == 'POST':
        form = AddItemForm(request.POST)
        amount = request.POST.get('amount')
        barcode = request.POST.get('barcode')

        if form.is_valid() and amount.isdigit():
            amount = int(amount)
            item, created = Item.objects.get_or_create(
                name=form.cleaned_data['name'],
                defaults={'quantity': 0, 'barcode': barcode}
            )
            item.quantity += amount
            item.save()
            messages.success(request, 'Item added successfully.')
            return redirect('index')
    else:
        form = AddItemForm()
    return render(request, 'inventory/add_item.html', {'form': form})

def remove_item(request):
    if request.method == 'POST':
        form = RemoveItemForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            quantity = form.cleaned_data['quantity']
            try:
                item = Item.objects.get(name=name)
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    item.save()
                    messages.success(request, 'Item removed successfully.')
                else:
                    messages.error(request, 'Not enough quantity to remove.')
            except Item.DoesNotExist:
                messages.error(request, 'Item not found.')
            return redirect('index')
    else:
        form = RemoveItemForm()
    return render(request, 'inventory/remove_item.html', {'form': form})
