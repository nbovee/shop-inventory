from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="checkout"),
    path("process_order/", views.process_order, name="process_order"),
]
