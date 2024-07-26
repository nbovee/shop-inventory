from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import BaseItem, Location, Inventory
from io import BytesIO
from django.http import HttpResponse


import uuid

from treepoem import generate_barcode
from PIL import Image

from .forms import (
    BaseItemForm,
    LocationForm,
    InventoryForm,
    RemoveInventoryForm,
    EditInventoryForm,
)


# @login_required
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
    return render(request, "inventory/manage_inventory.html")


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


@login_required
# @permission_required("add_baseitem", raise_exception=True)
def qrcode_sheet(request):
    dpi = 600

    page_width = int(8.5 * dpi)
    page_height = int(11.0 * dpi)
    # designed for Avery Presta 94503
    barcode_size = int(0.3 * dpi)
    barcode_spacing_x = int(0.72 * dpi)
    barcode_spacing_y = int(0.69 * dpi)

    barcode_rows = int(14)
    barcode_cols = int(11)

    barcode_offset_x = int(0.53 * dpi)
    barcode_offset_y = int(0.91 * dpi)

    sheet_img = Image.new("1", (page_width, page_height), 1)

    for row in range(0, barcode_rows):
        for col in range(0, barcode_cols):
            id = uuid.uuid4()
            # 22px sie is 1px target border, 20x20 data
            encoded = generate_barcode(
                barcode_type="qrcode",
                data=f"{id.hex}",
                options={"version": "3"},
                scale=1,
            )
            # scale 7.5 could be correct for this dpi but it takes int
            barcode_img = encoded.convert("1").resize((barcode_size, barcode_size))
            sheet_img.paste(
                barcode_img.copy(),
                (
                    barcode_offset_x + col * barcode_spacing_x,
                    barcode_offset_y + row * barcode_spacing_y,
                ),
            )

    bytes = BytesIO()
    sheet_img.save(bytes, "PDF", resolution=dpi)
    response = HttpResponse(bytes.getvalue(), content_type="application/pdf")
    return response
