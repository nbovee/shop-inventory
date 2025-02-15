from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add_inventory, name="add_inventory"),
    path("edit/<int:pk>/", views.edit_inventory, name="edit_inventory"),
    path("add_product/", views.add_product, name="add_product"),
    path("remove_product/", views.remove_product, name="remove_product"),
    path("add_location/", views.add_location, name="add_location"),
    path("remove_location/", views.remove_location, name="remove_location"),
    path("manage/", views.manage_inventory, name="manage_inventory"),
    path("barcodes", views.qrcode_sheet, name="barcodes"),
    path("stock_check/", views.stock_check, name="stock_check"),
    path("stock_update", views.stock_update, name="stock_update"),
    path("add-to-location/", views.add_item_to_location, name="add_item_to_location"),
    path("reactivate_product/", views.reactivate_product, name="reactivate_product"),
    path("reactivate_location/", views.reactivate_location, name="reactivate_location"),
]
