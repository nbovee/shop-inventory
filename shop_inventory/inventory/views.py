from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import BaseItem, Location, Inventory
from django.http import HttpResponse


from .forms import (
    BaseItemForm,
    LocationForm,
    InventoryForm,
    RemoveInventoryForm,
    EditInventoryForm,
    StockUpdateForm,
)

from .barcode_gen import barcode_page_generation


@login_required
def index(request):
    search_query = request.GET.get("search", None)
    if search_query:
        inventory_items = Inventory.objects.filter(
            Q(base_item__name__icontains=search_query)
            | Q(location__name__icontains=search_query)
        )
    else:
        inventory_items = Inventory.objects.all()
    return render(request, "inventory/index.html", {"inventory_items": inventory_items})


@login_required
def stock_check(request):
    locations = Location.objects.all()
    items_in_location = {}
    for location in locations:
        items_in_location[location] = Inventory.objects.filter(location=location)
    return render(
        request, "inventory/stock_check.html", {"items_in_location": items_in_location}
    )


@login_required
def stock_update(request, item=None, delta_qty=None):
    if request.method == "POST":
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            item = Inventory.objects.get(id=form.cleaned_data["item_id"])
            try:
                item.quantity += form.cleaned_data["delta_qty"]
                item.save()
                messages.success(request, "{} Updated.".format(item))
            except Exception:
                messages.failure(request, "{} could not be Updated.".format(item))
    return redirect("stock_check")


@login_required
def add_inventory(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        base_item = form.data["base_item"]
        location = form.data["location"]
        quantity = int(form.data["quantity"])
        try:
            inventory_item = Inventory.objects.get(
                base_item=base_item, location=location
            )
            inventory_item.quantity += quantity
            inventory_item.save()
            messages.success(request, "Inventory item quantity updated successfully.")
        except Inventory.DoesNotExist:
            if form.is_valid():
                Inventory.objects.create(
                    base_item=base_item, location=location, quantity=quantity
                )
                messages.success(request, "Inventory item added successfully.")
            else:
                messages.failure(request, "Inventory item could not be add/updated.")

        return redirect("inventory")
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
            return redirect("manage_inventory")
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
                base_item.active = False
                base_item.save()
                messages.success(request, "Base item removed successfully.")
            except BaseItem.DoesNotExist:
                messages.error(request, "Base item not found.")
            return redirect("manage_inventory")
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
            return redirect("manage_inventory")
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
                location.active = False
                location.save()
                messages.success(request, "Location removed successfully.")
            except Location.DoesNotExist:
                messages.error(request, "Location not found.")
            return redirect("manage_inventory")
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
            form.save(commit=True)
            messages.success(request, "Inventory item updated successfully.")
            return redirect("inventory")
    else:
        form = EditInventoryForm(instance=inventory_item)
    return render(
        request,
        "inventory/edit_item.html",
        {"form": form, "inventory_item": inventory_item},
    )


@login_required
# @permission_required("add_baseitem", raise_exception=True)
def qrcode_sheet(request):
    result = barcode_page_generation()
    response = HttpResponse(result, content_type="application/pdf")
    return response
