from django.urls import path

from . import views

app_name = 'checkout'
urlpatterns = [
    path('', views.index, name='index'),
    path('checkoutComplete/', views.checkoutComplete, name='checkoutComplete'),
]
