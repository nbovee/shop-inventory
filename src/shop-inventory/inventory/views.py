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
import uuid

from .forms import (
    AddProductForm,
    AddLocationForm,
    InventoryQuantityUpdateForm,
    DeactivateLocationForm,
    DeactivateProductForm,
    AddQuantityForm,
    NewProductForm,
    BarcodeForm,
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

    # Get all locations
    locations = Location.objects.all()
    items_in_location = {}

    for location in locations:
        # If search query exists, filter inventory items for this location
        if search_query:
            inventory_items = Inventory.objects.filter(
                Q(product__name__icontains=search_query)
                | Q(location__name__icontains=search_query),
                location=location,
            )
        else:
            inventory_items = Inventory.objects.filter(location=location)

        # Store the inventory items as 'list' attribute for the location
        location.list = inventory_items
        items_in_location[location] = location

    # Get recent orders if user has permission
    recent_orders = None
    if request.user.has_perm("inventory.add_product"):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = Order.objects.filter(date__gte=thirty_days_ago).order_by(
            "-date"
        )

    context = {"items_in_location": items_in_location, "recent_orders": recent_orders}

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
@permission_required("inventory.add_product", raise_exception=True)
def add_product(request):
    if request.method == "POST":
        form = AddProductForm(request.POST)
        try:
            if form.is_valid():
                # Extract location and quantity from form data
                location = form.cleaned_data["location"]
                quantity = form.cleaned_data["quantity"]

                # Create and save the product
                product = form.save(commit=False)
                # Use the barcode from the form (which was pre-generated)
                if not product.barcode:
                    product.barcode = str(uuid.uuid4().hex)
                product.save()

                # Create inventory entry
                inventory = Inventory(
                    product=product, location=location, quantity=quantity
                )
                inventory.save()

                messages.success(
                    request,
                    f"Product added successfully and {quantity} added to {location}.",
                )
                return redirect("inventory:add_product")
        except forms.ValidationError as e:
            if e.code == "reactivated":
                messages.success(request, str(e))
                return redirect("inventory:add_product")
            form.add_error(None, e)
    else:
        # Pre-generate barcode for new form
        initial_data = {"barcode": str(uuid.uuid4().hex)}
        form = AddProductForm(initial=initial_data)

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
            product = Product.objects.get(
                id=form.cleaned_data["product"].id, active=True
            )

            # Deactivate the product
            product.active = False
            product.save()

            messages.success(request, f"Product '{product}' deactivated successfully.")

            return redirect("inventory:remove_product")
    else:
        form = DeactivateProductForm()

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
        form = AddLocationForm(request.POST)
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
        form = AddLocationForm()

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
    """Show the location selection screen."""
    locations = Location.objects.filter(active=True).order_by("name")
    context = {
        "locations": locations,
        "form_type": "show_locations",
        "form_title": "Select a Location",
    }
    return render(request, "inventory/add_item_to_location.html", context)


def _handle_location(request, from_selection=False):
    """
    Handle location selection or continuation with a previously selected location. Always leads to the scan form.

    Parameters:
        request: The HTTP request
        from_selection: True if this is a new selection, False if continuing with existing.
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
            "form": BarcodeForm(),
            "form_type": "scan_form",
            "form_title": "Scan a Barcode",
        }

        return render(request, "inventory/add_item_to_location.html", context)
    except (KeyError, Location.DoesNotExist):
        # Invalid or missing data
        _clear_workflow_session(request)
        return redirect("inventory:add_item_to_location")


def _handle_scan_barcode(request):
    """
    Handle barcode scanning. Either leads to the quantity form or the new item form.
    """
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

    form = BarcodeForm(request.POST)
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
                context["form"] = BarcodeForm()
                context["form_type"] = "scan_form"
                context["form_title"] = "Scan a Barcode"
                return render(request, "inventory/add_item_to_location.html", context)

            # Store product ID in session
            request.session["current_product_id"] = product.id

            # Item exists, show quantity form
            context["product"] = product
            context["form"] = AddQuantityForm()
            context["form_type"] = "quantity_form"
            context["form_title"] = "Add Quantity"
        except Product.DoesNotExist:
            # Item doesn't exist, show new item form
            messages.warning(
                request,
                "New Item Detected: Please verify this is a new item and enter its details carefully.",
            )
            context["form"] = NewProductForm()
            context["barcode"] = barcode
            context["form_type"] = "new_item_form"
            context["form_title"] = "Enroll a New Item"
    else:
        messages.error(request, "Barcode appears to be invalid. Please try again.")

        # Form is invalid, show it again with errors
        context["form"] = form
        context["form_type"] = "scan_form"
        context["form_title"] = "Scan a Barcode"

    return render(request, "inventory/add_item_to_location.html", context)


def _handle_add_new_item(request):
    """
    Handle adding a new item. Always leads to the quantity form.
    """
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
    """
    Handle adding quantity to an existing item. Always leads to the scan form after completion, using continue_with_location.
    """
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
        "selected_location": selected_location,
        "product": product,
        "form": AddQuantityForm(),
        "form_type": "quantity_form",
    }

    form = AddQuantityForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        try:
            # Use get_or_create instead of get to handle both cases
            inventory_item, created = Inventory.objects.get_or_create(
                product=product, location=selected_location, defaults={"quantity": 0}
            )

            # Update the quantity
            inventory_item.quantity += quantity
            inventory_item.save()

            action_text = (
                "Added" if not created else "Created new inventory item and added"
            )
            messages.success(
                request,
                f"{action_text} {quantity} {product} to {inventory_item.location}",
            )

            # Item successfully added, return to scanning
            context["form"] = BarcodeForm()
            context["form_type"] = "scan_form"
            context["form_title"] = "Scan a Barcode"

            # Clear product-specific session data, but keep location
            _clear_product_session(request)
        except Exception as e:
            # Log the specific error
            messages.error(request, f"Error updating inventory: {str(e)}")
            # Debug information
            print(f"Error details: {type(e).__name__}: {str(e)}")
            # Keep the form as is to retry
            context["form"] = form
            context["form_type"] = "quantity_form"
    else:
        # If the form is invalid, show it again with errors
        context["form"] = form
        context["form_type"] = "quantity_form"

    return render(request, "inventory/add_item_to_location.html", context)


def _handle_cancel(request):
    """Handle cancellation of the workflow. Always leads to the index page."""
    _clear_workflow_session(request)
    return redirect("inventory:index")


def _clear_workflow_session(request):
    """Clear all session variables related to the add item workflow. Always leads to the index page."""
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
    """Clear product-related session variables but keep location. Always leads to the scan form."""
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
            product = Product.objects.get(id=form.cleaned_data["product"].id)
            product.active = True
            product.save()
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
            location = Location.objects.get(id=form.cleaned_data["location"].id)
            location.active = True
            location.save()
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
