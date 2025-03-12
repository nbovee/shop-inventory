from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Product, Location, Inventory, normalize_barcode
from checkout.models import Order
from django.http import HttpResponse
from django.core import exceptions as forms
from django.contrib.auth.decorators import permission_required

from .forms import (
    ProductForm,
    LocationForm,
    RemoveInventoryForm,
    StockUpdateForm,
    RemoveLocationForm,
    RemoveProductForm,
    AddItemToLocation,
    ProductFromBarcodeForm,
    ReactivateProductForm,
    ReactivateLocationForm,
    EditProductForm,
    SelectProductForm,
)

from .barcode_gen import barcode_page_generation


@login_required
@permission_required("inventory.view_inventory", raise_exception=True)
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
@permission_required("inventory.change_inventory", raise_exception=True)
def stock_check(request):
    locations = Location.objects.all()
    items_in_location = {}
    for location in locations:
        items_in_location[location] = Inventory.objects.filter(location=location)
    return render(
        request, "inventory/stock_check.html", {"items_in_location": items_in_location}
    )


@login_required
@permission_required("inventory.change_inventory", raise_exception=True)
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
@permission_required("inventory.delete_inventory", raise_exception=True)
def remove_inventory(request):
    if request.method == "POST":
        form = RemoveInventoryForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data["product"]
            location = form.cleaned_data["location"]
            quantity = form.cleaned_data["quantity"]
            try:
                inventory_item = Inventory.objects.get(
                    product=product, location=location, active=True
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
@permission_required("inventory.add_product", raise_exception=True)
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
@permission_required("inventory.delete_product", raise_exception=True)
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
        form = RemoveProductForm()

    # Get active products for context
    active_products = Product.objects.filter(active=True).order_by(
        "name", "manufacturer"
    )

    return render(
        request,
        "inventory/remove_product.html",
        {"form": form, "products": active_products},
    )


@login_required
@permission_required("inventory.add_location", raise_exception=True)
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
@permission_required("inventory.delete_location", raise_exception=True)
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
@permission_required("inventory.change_inventory", raise_exception=True)
def manage_inventory(request):
    return render(request, "inventory/manage_inventory.html")


@login_required
@permission_required("inventory.add_inventory", raise_exception=True)
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
@permission_required("inventory.add_inventory", raise_exception=True)
def add_item_to_location(request):
    # Simple dispatch pattern - both for GET and POST
    # For POST requests, get the action the user performed from form data
    if request.method == "POST":
        action = request.POST.get("action")
    # For GET requests, determine the action based on session state
    elif "selected_location_id" in request.session:
        # If there is a location in session, continue with that location
        action = "continue_with_location"
    else:
        # If there is no location in session, show the locations
        action = "show_locations"

    # Map actions to their handler functions
    action_handlers = {
        "show_locations": _handle_show_locations,
        "select_location": lambda req: _handle_location(req, from_selection=True),
        "continue_with_location": lambda req: _handle_location(
            req, from_selection=False
        ),
        "scan_barcode": _handle_scan_barcode,
        "add_new_item": _handle_add_new_item,
        "add_quantity": _handle_add_quantity,
        "cancel": _handle_cancel,  # Add the cancel handler
    }

    # Get the appropriate handler and execute it
    handler = action_handlers.get(action)
    if handler:
        return handler(request)
    else:
        # Invalid action, redirect to the start
        messages.error(request, "Invalid action")
        _clear_workflow_session(request)
        return redirect("inventory:add_item_to_location")


def _handle_show_locations(request):
    """Show the location selection screen"""
    locations = Location.objects.filter(active=True).order_by("name")
    context = {
        "locations": locations,
    }
    return render(request, "inventory/add_item_to_location.html", context)


def _handle_location(request, from_selection=False):
    """
    Handle location selection or continuation with a previously selected location

    Parameters:
        request: The HTTP request
        from_selection: True if this is a new selection, False if continuing with existing
    """
    try:
        # Get location ID either from POST (new selection) or session (continuation)
        if from_selection:
            location_id = request.POST.get("location_id")
            # Store new selection in session
            request.session["selected_location_id"] = location_id
        else:
            location_id = request.session.get("selected_location_id")

        # Get the location object
        selected_location = get_object_or_404(Location, id=location_id, active=True)

        # Set up context with scan form
        context = {
            "locations": Location.objects.filter(active=True).order_by("name"),
            "selected_location": selected_location,
            "form": AddItemToLocation(),
            "form_type": "scan_form",
        }

        return render(request, "inventory/add_item_to_location.html", context)
    except (KeyError, Location.DoesNotExist):
        # Invalid or missing data
        _clear_workflow_session(request)
        return redirect("inventory:add_item_to_location")


def _handle_scan_barcode(request):
    # Get location from session
    if "selected_location_id" not in request.session:
        messages.error(request, "No location selected. Please select a location first.")
        return redirect("inventory:add_item_to_location")

    selected_location = get_object_or_404(
        Location, id=request.session["selected_location_id"], active=True
    )

    context = {
        "selected_location": selected_location,
    }

    form = AddItemToLocation(request.POST)
    if form.is_valid():
        barcode = form.cleaned_data["barcode"]

        # Store barcode in session for next steps
        request.session["current_barcode"] = barcode

        # Normalize the scanned barcode
        normalized = normalize_barcode(barcode)
        try:
            # Search directly by normalized barcode
            product = Product.objects.get(normalized_barcode=normalized)

            # Check if the product is inactive
            if not product.active:
                messages.warning(
                    request,
                    f"Product '{product}' is inactive. Please consult with a Rowan Pantry Manager to reactivate it.",
                )
                context["form"] = AddItemToLocation()
                context["form_type"] = "scan_form"
                return render(request, "inventory/add_item_to_location.html", context)

            # Store product ID in session
            request.session["current_product_id"] = product.id

            # Item exists, show quantity form
            context["product"] = product
            context["form"] = AddQuantityForm()
            context["form_type"] = "quantity_form"
        except Product.DoesNotExist:
            # Item doesn't exist, show new item form
            messages.warning(
                request,
                "New Item Detected: Please verify this is a new item and enter its details carefully.",
            )
            context["form"] = NewProductForm()
            context["barcode"] = barcode
            context["form_type"] = "new_item_form"
    else:
        messages.error(request, "Barcode appears to be invalid. Please try again.")

        # Form is invalid, show it again with errors
        context["form"] = form
        context["form_type"] = "scan_form"

    return render(request, "inventory/add_item_to_location.html", context)


def _handle_add_new_item(request):
    # Get location from session
    if (
        "selected_location_id" not in request.session
        or "current_barcode" not in request.session
    ):
        messages.error(request, "Session data missing. Please restart the process.")
        _clear_workflow_session(request)
        return redirect("inventory:add_item_to_location")

    location_id = request.session["selected_location_id"]
    selected_location = get_object_or_404(Location, id=location_id, active=True)
    barcode = request.session["current_barcode"]

    context = {
        "locations": Location.objects.filter(active=True).order_by("name"),
        "selected_location": selected_location,
        "barcode": barcode,
    }

    form = NewProductForm(request.POST)
    if form.is_valid():
        product = form.save(commit=False)
        product.barcode = barcode
        product.save()

        # Store product ID in session for the quantity step
        request.session["current_product_id"] = product.id
        context["product"] = product
        context["form"] = AddQuantityForm()
        context["form_type"] = "quantity_form"
    else:
        # If form is invalid, show it again with errors
        context["form"] = form
        context["form_type"] = "new_item_form"

    return render(request, "inventory/add_item_to_location.html", context)


def _handle_add_quantity(request):
    # Get data from session
    if (
        "selected_location_id" not in request.session
        or "current_product_id" not in request.session
    ):
        messages.error(request, "Session data missing. Please restart the process.")
        _clear_workflow_session(request)
        return redirect("inventory:add_item_to_location")

    location_id = request.session["selected_location_id"]
    product_id = request.session["current_product_id"]

    selected_location = get_object_or_404(Location, id=location_id, active=True)
    product = get_object_or_404(Product, id=product_id)

    context = {
        "locations": Location.objects.filter(active=True).order_by("name"),
        "selected_location": selected_location,
        "product": product,
    }

    form = AddQuantityForm(request.POST, product=product, location=selected_location)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]

        # Handle reactivation of inactive inventory
        if "reactivate_item" in form.cleaned_data:
            inventory_item = form.cleaned_data["reactivate_item"]
            inventory_item.quantity = quantity
            inventory_item.active = True
            inventory_item.save()
            messages.success(
                request,
                f"Reactivated inventory item with quantity {quantity}",
            )
        else:
            # Normal create/update flow
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
                f"Added {quantity} {product} to {inventory_item.location}",
            )

        # Item successfully added, return to scanning
        context["form"] = AddItemToLocation()
        context["form_type"] = "scan_form"

        # Clear product-specific session data, but keep location
        _clear_product_session(request)
    else:
        # If the form is invalid, show it again with errors
        context["form"] = form
        context["form_type"] = "quantity_form"

    return render(request, "inventory/add_item_to_location.html", context)


def _handle_cancel(request):
    """Handle cancellation of the workflow"""
    _clear_workflow_session(request)
    return redirect("inventory:index")


def _clear_workflow_session(request):
    """Clear all session variables related to the add item workflow"""
    keys_to_clear = [
        "selected_location_id",
        "current_barcode",
        "current_product_id",
        "form_type",
    ]
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]


def _clear_product_session(request):
    """Clear product-related session variables but keep location"""
    keys_to_clear = [
        "current_barcode",
        "current_product_id",
        "form_type",
    ]
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]


@login_required
@permission_required("inventory.change_product", raise_exception=True)
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
@permission_required("inventory.change_location", raise_exception=True)
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
@permission_required("inventory.change_product", raise_exception=True)
def edit_product(request):
    if request.method == "POST":
        action = request.POST.get("action")

        # Handle product selection
        if action == "select_product":
            form = SelectProductForm(request.POST)
            if form.is_valid():
                product = form.cleaned_data["product"]
                # Store selected product in session for edit form
                request.session["edit_product_id"] = product.id
                edit_form = EditProductForm(instance=product)
                return render(
                    request,
                    "inventory/edit_product.html",
                    {"form": edit_form, "product": product, "form_type": "edit"},
                )

        # Handle product editing
        elif action == "edit_product":
            if "edit_product_id" not in request.session:
                messages.error(
                    request, "No product selected. Please select a product first."
                )
                return redirect("inventory:edit_product")

            product = get_object_or_404(Product, id=request.session["edit_product_id"])
            form = EditProductForm(request.POST, instance=product)

            if form.is_valid():
                form.save()
                messages.success(request, f"Product '{product}' updated successfully.")
                # Clear session and redirect to start again
                if "edit_product_id" in request.session:
                    del request.session["edit_product_id"]
                return redirect("inventory:edit_product")
            else:
                # Form is invalid, show with errors
                return render(
                    request,
                    "inventory/edit_product.html",
                    {"form": form, "product": product, "form_type": "edit"},
                )

        # Handle cancellation
        elif action == "cancel":
            if "edit_product_id" in request.session:
                del request.session["edit_product_id"]
            messages.info(request, "Edit cancelled.")
            return redirect("inventory:edit_product")

    # Initial GET request or after completion
    if "edit_product_id" in request.session:
        del request.session["edit_product_id"]

    # Show product selection form
    form = SelectProductForm()
    return render(
        request, "inventory/edit_product.html", {"form": form, "form_type": "select"}
    )
