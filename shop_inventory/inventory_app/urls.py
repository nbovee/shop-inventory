# inventory_app/inventory_app/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),  # Include the app's URL configurations
]

