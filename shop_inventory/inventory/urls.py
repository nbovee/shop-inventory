from django.urls import path
#from . import views
from .views import Index, InventoryList, AddInventory, DeleteInventory, EditInventory

app_name = "inventory"

urlpatterns = [
    path("", Index.as_view(), name="Index"),
    # path("", views.index, name="index"),
    path("inventorylist/", InventoryList.as_view(), name="InventoryList"),
    path("add_inventory", AddInventory.as_view(), name="AddInventory"),
    path("delete_inventory/<int:pk>/", DeleteInventory.as_view(), name="DeleteInventory"),
    path("edit_inventory/<int:pk>/", EditInventory.as_view(template_name="inventory/edit_inventory.html"), name="EditInventory"),
]
