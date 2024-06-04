# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomAdmin(UserAdmin):
    pass


#     # Add custom fields here
#     list_display = ("email", "is_staff")
#     fieldsets = (
#         (None, {"fields": ("email", "password")}),
#         ("Personal info", {"fields": ("first_name", "last_name")}),
#         ("Permissions", {"fields": ("is_staff", "is_active")}),
#     )
