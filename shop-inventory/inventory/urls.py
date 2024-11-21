from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="inventory"),
    path("add/", views.add_inventory, name="add_inventory"),
    path("edit/<int:pk>/", views.edit_inventory, name="edit_inventory"),
    path("add_base_item/", views.add_base_item, name="add_base_item"),
    path("remove_base_item/", views.remove_base_item, name="remove_base_item"),
    path("add_location/", views.add_location, name="add_location"),
    path("remove_location/", views.remove_location, name="remove_location"),
    path("manage/", views.manage_base_items_locations, name="manage_inventory"),
    path("barcodes", views.qrcode_sheet, name="barcodes"),
    path("stockcheck/", views.stock_check, name="stock_check"),
    path("stock_update", views.stock_update, name="stock_update"),
]
