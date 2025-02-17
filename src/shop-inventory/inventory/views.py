from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Product,
    Location,
    Inventory,
    ProductUUID,
    barcode_is_uuid,
    normalize_barcode,
)
from checkout.models import Order
from django.http import HttpResponse
from django.core import exceptions as forms
import uuid


from .forms import (
    ProductForm,
    LocationForm,
    InventoryQuantityUpdateForm,
    DeactivateLocationForm,
    DeactivateProductForm,
    AddItemToLocation,
    ProductFromBarcodeForm,
    ReactivateProductForm,
    ReactivateLocationForm,
    UUIDItemForm,
    LinkUUIDForm,
)

from .barcode_gen import barcode_page_generation


@login_required
def index(request):
    search_query = request.GET.get("search", None)
    if search_query:
        inventory_items = Inventory.objects.filter(
            Q(product__name__icontains=search_query)
            | Q(location__name__icontains=search_query)
        )
    else:
        inventory_items = Inventory.objects.all()

    # Get recent orders if user has permission
    recent_orders = None
    if request.user.has_perm("inventory.add_product"):
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
        form = InventoryQuantityUpdateForm(request.POST)
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
                    # If product is inactive and quantity reaches 0, deactivate inventory item
                    if new_quantity == 0 and not item.product.active:
                        item.active = False
                        messages.info(
                            request,
                            f"{item} has been deactivated as its product was marked for removal.",
                        )
                    item.save()
                    messages.success(
                        request, f"{item} updated to quantity {new_quantity}."
                    )
            except Exception as e:
                messages.error(request, f"{item} could not be updated: {str(e)}")
    return redirect("inventory:stock_check")


@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Product added successfully.")
                return redirect("inventory:add_product")
        except forms.ValidationError as e:
            if e.code == "reactivated":
                messages.success(request, str(e))
                return redirect("inventory:add_product")
            form.add_error(None, e)
    else:
        form = ProductForm()

    # Get list of inactive items for reference
    inactive_items = Product.objects.filter(active=False).order_by(
        "name", "manufacturer"
    )

    return render(
        request,
        "inventory/add_product.html",
        {"form": form, "inactive_items": inactive_items},
    )


@login_required
def remove_product(request):
    if request.method == "POST":
        form = DeactivateProductForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data["product"]

            # Get all active inventory items for this product
            inventory_items = Inventory.objects.filter(product=product, active=True)

            # Deactivate the product
            product.deactivate()

            # Handle inventory items
            if inventory_items.exists():
                inventory_count = inventory_items.count()
                zero_quantity_count = inventory_items.filter(quantity=0).update(
                    active=False
                )
                remaining_count = inventory_count - zero_quantity_count

                if remaining_count > 0:
                    messages.warning(
                        request,
                        f"Product '{product}' deactivated. {remaining_count} inventory items still have stock "
                        "and will be deactivated when they reach zero quantity.",
                    )
                else:
                    messages.success(
                        request,
                        f"Product '{product}' and all its inventory items have been deactivated.",
                    )
            else:
                messages.success(
                    request, f"Product '{product}' deactivated successfully."
                )

            return redirect("inventory:remove_product")
    else:
        form = DeactivateProductForm()
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
        form = DeactivateLocationForm(request.POST)
        if form.is_valid():
            location = form.cleaned_data["location"]
            if Inventory.objects.filter(location=location, active=True).exists():
                messages.error(
                    request, "Cannot remove location that has active products."
                )
            else:
                location.active = False
                location.save()
                messages.success(
                    request, f"Location '{location.name}' removed successfully."
                )
            return redirect("inventory:remove_location")
    else:
        form = DeactivateLocationForm()
    return render(request, "inventory/remove_location.html", {"form": form})


@login_required
def manage_inventory(request):
    return render(request, "inventory/manage_inventory.html")


@login_required
# @permission_required("add_product", raise_exception=True)
def qrcode_sheet(request):
    result = barcode_page_generation(pages=10)
    response = HttpResponse(result, content_type="application/pdf")
    return response


def handle_process_barcode(request, form, selected_location, context):
    barcode = form.cleaned_data["barcode"]

    if barcode_is_uuid(barcode):
        return handle_uuid_barcode(request, barcode, selected_location, context)
    else:
        return handle_upc_barcode(request, barcode, selected_location, context)


def handle_uuid_barcode(request, barcode, selected_location, context):
    if "current_base_item" in request.session:
        base_item = Product.objects.get(pk=request.session["current_base_item"])
        ProductUUID.objects.create(base_item=base_item, uuid_barcode=barcode)
        inventory_item, created = Inventory.objects.get_or_create(
            base_item=base_item,
            location=selected_location,
            defaults={"quantity": 1, "active": True},
        )
        if not created:
            inventory_item.quantity += 1
            inventory_item.save()

        messages.success(
            request,
            f"Added UUID barcode to {base_item}. Scan another UUID barcode to add it to the same product, or click 'Finish Linking' to complete the process.",
        )
        context.update(
            {
                "scan_form": AddItemToLocation(),
                "current_base_item": base_item,
                "show_finish_button": True,
            }
        )
    else:
        context["uuid_barcode"] = barcode
        context["link_form"] = LinkUUIDForm()
        context["scan_form"] = AddItemToLocation(request.POST)
        messages.info(
            request,
            f"Scanned UUID barcode {barcode}. Please select an existing product to link this barcode to, or create a new product.",
        )
    return render(request, "inventory/add_item_to_location.html", context)


def handle_upc_barcode(request, barcode, selected_location, context):
    try:
        base_item = Product.objects.get(normalized_barcode=normalize_barcode(barcode))
        context["base_item"] = base_item
        context["quantity_form"] = InventoryQuantityUpdateForm()
        context["scan_form"] = AddItemToLocation(request.POST)
        return render(request, "inventory/add_item_to_location.html", context)
    except Product.DoesNotExist:
        context["new_item_form"] = ProductFromBarcodeForm()
        context["barcode"] = barcode
        context["scan_form"] = AddItemToLocation(request.POST)
        messages.info(
            request,
            f"Scanned new barcode {barcode}. Please enter the details for the new product.",
        )
        return render(request, "inventory/add_item_to_location.html", context)


def handle_add_new_item(request, form, barcode, selected_location, context):
    base_item = form.save(commit=False)

    if barcode_is_uuid(barcode):
        base_item.barcode = str(uuid.uuid4().hex)
        base_item.save()
        ProductUUID.objects.create(base_item=base_item, uuid_barcode=barcode)
        Inventory.objects.create(
            base_item=base_item,
            location=selected_location,
            quantity=1,
            active=True,
        )
        messages.success(
            request,
            f"Created new product {base_item} and linked UUID barcode. Save this sticker in the Product Binder to easily scan it in the future. Scan another UUID barcode to add it to the same product, or click 'Finish Linking' to complete the process.",
        )
    else:
        base_item.barcode = barcode
        base_item.save()
        context.update(
            {
                "base_item": base_item,
                "quantity_form": InventoryQuantityUpdateForm(),
                "scan_form": AddItemToLocation(),
            }
        )
        messages.success(
            request,
            f"Created new product {base_item} with barcode {barcode}. Please enter the quantity to add to the selected location.",
        )
        return render(request, "inventory/add_item_to_location.html", context)

    context["scan_form"] = AddItemToLocation()
    return render(request, "inventory/add_item_to_location.html", context)


def handle_add_quantity(request, form, selected_location, context):
    quantity = form.cleaned_data["quantity"]

    if "reactivate_item" in form.cleaned_data:
        inventory_item = form.cleaned_data["reactivate_item"]
        inventory_item.quantity = quantity
        inventory_item.active = True
        inventory_item.save()
        messages.success(
            request,
            f"Reactivated inventory item with quantity {quantity}. Scan another barcode to continue adding items, or choose a different location.",
        )
    else:
        product = form.cleaned_data["product"]
        inventory_item, created = Inventory.objects.get_or_create(
            product=product,
            location=selected_location,
            defaults={"quantity": quantity, "active": True},
        )
        if not created:
            inventory_item.quantity += quantity
            inventory_item.save()
        messages.success(
            request,
            f"Added {quantity} {product} to {inventory_item.location}. Scan another barcode to continue adding items, or choose a different location.",
        )

    context["scan_form"] = AddItemToLocation()
    return render(request, "inventory/add_item_to_location.html", context)


def handle_link_uuid(request, form, uuid_barcode, selected_location, context):
    if request.POST.get("create_new"):
        context.update(
            {
                "new_item_form": ProductFromBarcodeForm(),
                "barcode": uuid_barcode,
                "scan_form": AddItemToLocation(),
                "barcode_is_uuid": True,
            }
        )
        return render(request, "inventory/add_item_to_location.html", context)

    if form.is_valid():
        base_item = form.cleaned_data["base_item"]
        ProductUUID.objects.create(base_item=base_item, uuid_barcode=uuid_barcode)
        inventory_item, created = Inventory.objects.get_or_create(
            base_item=base_item,
            location=selected_location,
            defaults={"quantity": 1, "active": True},
        )
        if not created:
            inventory_item.quantity += 1
            inventory_item.save()

        request.session["current_base_item"] = base_item.pk
        messages.success(
            request,
            f"UUID barcode linked to {base_item} and added to inventory. Scan another UUID barcode to add it to the same product, or click 'Finish Linking' to complete the process.",
        )
        context.update(
            {
                "scan_form": AddItemToLocation(),
                "current_base_item": base_item,
                "show_finish_button": True,
            }
        )
    else:
        context.update(
            {
                "uuid_barcode": uuid_barcode,
                "link_form": form,
                "scan_form": AddItemToLocation(),
            }
        )
    return render(request, "inventory/add_item_to_location.html", context)


def handle_finish_uuid_linking(request, context):
    if "current_base_item" in request.session:
        del request.session["current_base_item"]
    context["scan_form"] = AddItemToLocation()
    messages.success(
        request,
        "Finished linking UUID barcodes. Scan another barcode to continue adding items, or choose a different location.",
    )
    return render(request, "inventory/add_item_to_location.html", context)


@login_required
def add_item_to_location(request):
    locations = Location.objects.filter(active=True).order_by("name")
    selected_location = None
    if request.GET.get("location"):
        selected_location = get_object_or_404(
            Location, id=request.GET.get("location"), active=True
        )

    context = {
        "locations": locations,
        "selected_location": selected_location,
    }

    if selected_location:
        if request.method == "POST":
            action = request.POST.get("action")

            if action == "process_barcode":
                form = AddItemToLocation(request.POST)
                if form.is_valid():
                    return handle_process_barcode(
                        request, form, selected_location, context
                    )

            elif action == "add_new_item":
                form = ProductFromBarcodeForm(request.POST)
                barcode = request.POST.get("barcode")
                if form.is_valid():
                    return handle_add_new_item(
                        request, form, barcode, selected_location, context
                    )

            elif action == "add_quantity":
                product = get_object_or_404(Product, id=request.POST.get("product_id"))
                form = InventoryQuantityUpdateForm(
                    request.POST, product=product, location=selected_location
                )
                if form.is_valid():
                    return handle_add_quantity(
                        request, form, selected_location, context
                    )

            elif action == "link_uuid":
                link_form = LinkUUIDForm(request.POST)
                uuid_barcode = request.POST.get("uuid_barcode")
                return handle_link_uuid(
                    request, link_form, uuid_barcode, selected_location, context
                )

            elif action == "finish_uuid_linking":
                return handle_finish_uuid_linking(request, context)

        else:
            context["scan_form"] = AddItemToLocation()

    return render(request, "inventory/add_item_to_location.html", context)


@login_required
def reactivate_product(request):
    if request.method == "POST":
        form = ReactivateProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product}' reactivated successfully.")
            return redirect("inventory:reactivate_product")
    else:
        form = ReactivateProductForm()
    return render(request, "inventory/reactivate_product.html", {"form": form})


@login_required
def reactivate_location(request):
    if request.method == "POST":
        form = ReactivateLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(
                request, f"Location '{location.name}' reactivated successfully."
            )
            return redirect("inventory:reactivate_location")
    else:
        form = ReactivateLocationForm()
    return render(request, "inventory/reactivate_location.html", {"form": form})


@login_required
def add_uuid_item(request):
    if request.method == "POST":
        form = UUIDItemForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "UUID barcode added successfully.")
                return redirect("inventory:add_uuid_item")
        except forms.ValidationError as e:
            if e.code == "reactivated":
                messages.success(request, str(e))
                return redirect("inventory:add_uuid_item")
            form.add_error(None, e)
    else:
        form = UUIDItemForm()

    return render(request, "inventory/add_uuid_item.html", {"form": form})
