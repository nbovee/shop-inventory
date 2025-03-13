# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomAdmin(UserAdmin):
    # Add custom fields here
    list_display = ("username", "is_active", "get_groups")
    list_filter = ("is_active", "groups")
    search_fields = ("username",)
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups")},
        ),
    )

    @admin.display(description="Groups")
    def get_groups(self, obj):
        """Return a comma-separated list of the user's groups"""
        return ", ".join([group.name for group in obj.groups.all()])
