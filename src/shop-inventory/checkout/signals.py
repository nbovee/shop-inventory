# Default Locations
from django.dispatch import receiver
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Order


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
def create_shop_manager_permissions(sender, **kwargs):
    if sender.label == "checkout":
        group, created = Group.objects.get_or_create(name="Shop Manager")
        models = [Order]  # Add other related models as needed
        add_models_permissions(group, models, ["add", "change", "delete", "view"])
