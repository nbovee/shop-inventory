# inventory_app/inventory/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_inventory, name='add_inventory'),
    path('remove/', views.remove_inventory, name='remove_inventory'),
    path('login/', views.user_login, name='login'),
]

