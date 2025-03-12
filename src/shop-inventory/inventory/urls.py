from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.index, name="index"),
    path("add_product/", views.add_product, name="add_product"),
    path("add_location/", views.add_location, name="add_location"),
    path("edit_product/", views.edit_product, name="edit_product"),
    path("remove_product/", views.remove_product, name="remove_product"),
    path("remove_location/", views.remove_location, name="remove_location"),
    path("reactivate_product/", views.reactivate_product, name="reactivate_product"),
    path("reactivate_location/", views.reactivate_location, name="reactivate_location"),
    path("manager/", views.manage_inventory, name="manage_inventory"),
    path("barcodes", views.qrcode_sheet, name="barcodes"),
    path("stock_check/", views.stock_check, name="stock_check"),
    path("stock_update", views.stock_update, name="stock_update"),
    path("add-to-location/", views.add_item_to_location, name="add_item_to_location"),
    ]
