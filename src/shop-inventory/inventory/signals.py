# Default Locations
from django.dispatch import receiver
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Product, Location, Inventory
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_migrate)
def create_default_locations(sender, **kwargs):
    if sender.label == "inventory":
        locations = [
            {"name": "Shopfloor"},
            {"name": "Storage"},
        ]
        for loc in locations:
            location, created = Location.objects.get_or_create(name=loc["name"])
            if created:
                print(f'Location "{location.name}" created.')
            else:
                print(f'Location "{location.name}" already exists.')


def add_models_permissions(group, models, permissions):
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        permission_create = [
            Permission.objects.get(
                content_type=content_type,
                codename=f"{permission}_{model._meta.model_name}",
            )
            for permission in permissions
        ]
        group.permissions.add(*permission_create)
        group.save()
        print(
            f'permissions "{permissions}" for "{model._meta.model_name}" added to "{group.name}".'
        )


@receiver(post_migrate)
def create_shop_employee_permissions(sender, **kwargs):
    if sender.label == "inventory":
        group, created = Group.objects.get_or_create(name="Shop Employee")
        models = [Inventory, Product]  # Add other related models as needed
        add_models_permissions(group, models, ["add", "change", "view"])


@receiver(post_migrate)
def create_shop_manager_permissions(sender, **kwargs):
    if sender.label == "inventory":
        group, created = Group.objects.get_or_create(name="Shop Manager")
        models = [Inventory, Product, Location]  # Add other related models as needed
        add_models_permissions(group, models, ["add", "change", "delete", "view"])
