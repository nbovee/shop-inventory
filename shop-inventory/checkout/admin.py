from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem

# Register your models here.
admin.site.register((Order, OrderItem, Cart, CartItem))
