from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import BaseItem, Location, Inventory
from checkout.models import Order
from django.http import HttpResponse
from django.core import exceptions as forms


from .forms import (
    BaseItemForm,
    LocationForm,
    AddInventoryForm,
    RemoveInventoryForm,
    EditInventoryForm,
    StockUpdateForm,
    RemoveLocationForm,
    RemoveBaseItemForm,
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

    # Get recent orders if user has permission
    recent_orders = None
    if request.user.has_perm("inventory.add_baseitem"):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = Order.objects.filter(date__gte=thirty_days_ago).order_by(
            "-date"
        )

    context = {"inventory_items": inventory_items, "recent_orders": recent_orders}

    return render(request, "inventory/index.html", context)


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
def stock_update(request):
    if request.method == "POST":
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            item = Inventory.objects.get(id=form.cleaned_data["item_id"])
            try:
                new_quantity = item.quantity + form.cleaned_data["delta_qty"]
                if new_quantity < 0:
                    messages.error(
                        request, f"Cannot reduce quantity below 0 for {item}"
                    )
                else:
                    item.quantity = new_quantity
                    # If base item is inactive and quantity reaches 0, deactivate inventory item
                    if new_quantity == 0 and not item.base_item.active:
                        item.active = False
                        messages.info(
                            request,
                            f"{item} has been deactivated as its base item was marked for removal.",
                        )
                    item.save()
                    messages.success(
                        request, f"{item} updated to quantity {new_quantity}."
                    )
            except Exception as e:
                messages.error(request, f"{item} could not be updated: {str(e)}")
    return redirect("inventory:stock_check")


@login_required
def add_inventory(request):
    if request.method == "POST":
        form = AddInventoryForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Inventory item added successfully.")
                return redirect("inventory:add_inventory")
        except forms.ValidationError as e:
            if e.code == "reactivated":
                messages.success(request, str(e))
                return redirect("inventory:add_inventory")
            elif e.code == "updated":
                messages.success(request, str(e))
                return redirect("inventory:add_inventory")
            form.add_error(None, e)
    else:
        form = AddInventoryForm()
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
                    base_item=base_item, location=location, active=True
                )
                if inventory_item.quantity >= quantity:
                    inventory_item.quantity -= quantity
                    inventory_item.save()
                    messages.success(request, "Inventory item removed successfully.")
                else:
                    messages.error(request, "Not enough quantity to remove.")
            except Inventory.DoesNotExist:
                messages.error(request, "Inventory item not found.")
            return redirect("inventory:remove_inventory")
    else:
        form = RemoveInventoryForm()
    return render(request, "inventory/remove_item.html", {"form": form})


@login_required
def add_base_item(request):
    if request.method == "POST":
        form = BaseItemForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Base item added successfully.")
                return redirect("inventory:add_base_item")
        except forms.ValidationError as e:
            if e.code == "reactivated":
                messages.success(request, str(e))
                return redirect("inventory:add_base_item")
            form.add_error(None, e)
    else:
        form = BaseItemForm()

    # Get list of inactive items for reference
    inactive_items = BaseItem.objects.filter(active=False).order_by("name", "variant")

    return render(
        request,
        "inventory/add_base_item.html",
        {"form": form, "inactive_items": inactive_items},
    )


@login_required
def remove_base_item(request):
    if request.method == "POST":
        form = RemoveBaseItemForm(request.POST)
        if form.is_valid():
            base_item = form.cleaned_data["base_item"]

            # Get all active inventory items for this base item
            inventory_items = Inventory.objects.filter(base_item=base_item, active=True)

            # Deactivate the base item
            base_item.deactivate()

            # Handle inventory items
            if inventory_items.exists():
                # Prevent adding more quantity to these items
                inventory_count = inventory_items.count()
                zero_quantity_count = inventory_items.filter(quantity=0).update(
                    active=False
                )
                remaining_count = inventory_count - zero_quantity_count

                if remaining_count > 0:
                    messages.warning(
                        request,
                        f"Base item '{base_item}' deactivated. {remaining_count} inventory items still have stock "
                        "and will be deactivated when they reach zero quantity.",
                    )
                else:
                    messages.success(
                        request,
                        f"Base item '{base_item}' and all its inventory items have been deactivated.",
                    )
            else:
                messages.success(
                    request, f"Base item '{base_item}' deactivated successfully."
                )

            return redirect("inventory:remove_base_item")
    else:
        form = RemoveBaseItemForm()
    return render(request, "inventory/remove_base_item.html", {"form": form})


@login_required
def add_location(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Location added successfully.")
                return redirect("inventory:add_location")
        except forms.ValidationError as e:
            if e.code == "reactivated":
                messages.success(request, str(e))
                return redirect("inventory:add_location")
            form.add_error("name", e)
    else:
        form = LocationForm()

    # Get list of inactive locations for reference
    inactive_locations = Location.objects.filter(active=False).order_by("name")

    return render(
        request,
        "inventory/add_location.html",
        {"form": form, "inactive_locations": inactive_locations},
    )


@login_required
def remove_location(request):
    if request.method == "POST":
        form = RemoveLocationForm(request.POST)
        if form.is_valid():
            location = form.cleaned_data["location"]
            if Inventory.objects.filter(location=location).exists():
                messages.error(
                    request, "Cannot remove location that has inventory items."
                )
            else:
                location.active = False
                location.save()
                messages.success(
                    request, f"Location '{location.name}' removed successfully."
                )
            return redirect("inventory:remove_location")
    else:
        form = RemoveLocationForm()
    return render(request, "inventory/remove_location.html", {"form": form})


@login_required
def manage_inventory(request):
    return render(request, "inventory/manage_inventory.html")


@login_required
def edit_inventory(request, pk):
    inventory_item = get_object_or_404(Inventory, pk=pk)
    if request.method == "POST":
        form = EditInventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, "Inventory item updated successfully.")
            return redirect("inventory:index")
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
