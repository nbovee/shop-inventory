from django.urls import path

from . import views

app_name = "checkout"

urlpatterns = [
    path("", views.index, name="index"),
    path("process/", views.process_order, name="process_order"),
    path("recent/", views.recent_orders, name="recent_orders"),
]
