from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import BaseItem, Location, Inventory
from .forms import (
    BaseItemForm,
    LocationForm,
    InventoryForm,
    RemoveInventoryForm,
    EditInventoryForm,
)


# @login_required
def index(request):
    search_query = request.GET.get("search", "")
    if search_query:
        inventory_items = Inventory.objects.filter(
            Q(base_item__name__icontains=search_query)
            | Q(location__name__icontains=search_query)
        )
    else:
        inventory_items = Inventory.objects.all()
    return render(request, "inventory/index.html", {"inventory_items": inventory_items})


# @login_required
def add_inventory(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            base_item = form.cleaned_data["base_item"]
            location = form.cleaned_data["location"]
            quantity = form.cleaned_data["quantity"]

            try:
                inventory_item = Inventory.objects.get(
                    base_item=base_item, location=location
                )
                inventory_item.quantity += quantity
                inventory_item.save()
                messages.success(
                    request, "Inventory item quantity updated successfully."
                )
            except Inventory.DoesNotExist:
                Inventory.objects.create(
                    base_item=base_item, location=location, quantity=quantity
                )
                messages.success(request, "Inventory item added successfully.")

            return redirect("index")
    else:
        form = InventoryForm()
    return render(request, "inventory/add_item.html", {"form": form})


@login_required
def remove_inventory(request):
    if request.method == "POST":
        form = RemoveInventoryForm(request.POST)
        if form.is_valid():
            base_item = form.cleaned_data["base_item"]
            location = form.cleaned_data["location"]
            quantity = form.cleaned_data["quantity"]
            try:
                inventory_item = Inventory.objects.get(
                    base_item=base_item, location=location
                )
                if inventory_item.quantity >= quantity:
                    inventory_item.quantity -= quantity
                    if inventory_item.quantity == 0:
                        inventory_item.delete()
                    else:
                        inventory_item.save()
                    messages.success(request, "Inventory item removed successfully.")
                else:
                    messages.error(request, "Not enough quantity to remove.")
            except Inventory.DoesNotExist:
                messages.error(request, "Inventory item not found.")
            return redirect("index")
    else:
        form = RemoveInventoryForm()
    return render(request, "inventory/remove_item.html", {"form": form})


@login_required
def add_base_item(request):
    if request.method == "POST":
        form = BaseItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Base item added successfully.")
            return redirect("manage_base_items_locations")
    else:
        form = BaseItemForm()
    return render(request, "inventory/add_base_item.html", {"form": form})


@login_required
def remove_base_item(request):
    if request.method == "POST":
        form = BaseItemForm(request.POST)
        if form.is_valid():
            base_item_name = form.cleaned_data["name"]
            try:
                base_item = BaseItem.objects.get(name=base_item_name)
                base_item.delete()
                messages.success(request, "Base item removed successfully.")
            except BaseItem.DoesNotExist:
                messages.error(request, "Base item not found.")
            return redirect("manage_base_items_locations")
    else:
        form = BaseItemForm()
    return render(request, "inventory/remove_base_item.html", {"form": form})


@login_required
def add_location(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location added successfully.")
            return redirect("manage_base_items_locations")
    else:
        form = LocationForm()
    return render(request, "inventory/add_location.html", {"form": form})


@login_required
def remove_location(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            location_name = form.cleaned_data["name"]
            try:
                location = Location.objects.get(name=location_name)
                location.delete()
                messages.success(request, "Location removed successfully.")
            except Location.DoesNotExist:
                messages.error(request, "Location not found.")
            return redirect("manage_base_items_locations")
    else:
        form = LocationForm()
    return render(request, "inventory/remove_location.html", {"form": form})


@login_required
def manage_base_items_locations(request):
    return render(request, "inventory/manage_base_items_locations.html")


@login_required
def edit_inventory(request, pk):
    inventory_item = get_object_or_404(Inventory, pk=pk)
    if request.method == "POST":
        form = EditInventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item updated successfully.")
            return redirect("index")
    else:
        form = EditInventoryForm(instance=inventory_item)
    return render(
        request,
        "inventory/edit_item.html",
        {"form": form, "inventory_item": inventory_item},
    )


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "inventory/login.html")


def user_logout(request):
    logout(request)
    return redirect("login")
