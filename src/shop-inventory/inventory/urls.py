from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.index, name="index"),
    path("add-to-location/", views.add_item_to_location, name="add_item_to_location"),
    path("add/location/", views.add_location, name="add_location"),
    path("add/product/", views.add_product, name="add_product"),
    path("barcodes/", views.qrcode_sheet, name="barcodes"),
    path("manage/", views.manage_inventory, name="manage_inventory"),
    path("reactivate/location/", views.reactivate_location, name="reactivate_location"),
    path("reactivate/product/", views.reactivate_product, name="reactivate_product"),
    path("remove/location/", views.remove_location, name="remove_location"),
    path("remove/product/", views.remove_product, name="remove_product"),
    path("stock_check/", views.stock_check, name="stock_check"),
    path("stock_update/", views.stock_update, name="stock_update"),
]
