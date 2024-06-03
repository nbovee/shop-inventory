# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Add custom fields here
    list_display = ("email", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("firstname", "lastname")}),
        ("Permissions", {"fields": ("is_staff", "is_active")}),
    )
