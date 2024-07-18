# Define Required Permissions and Groups for the App to run after migration
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Inventory, BaseItem, Location

# Create Shop Employee Group
@receiver(post_migrate)
def create_shop_employee_group(sender, **kwargs):
    if sender.label == "users":
        # Create the group
        group, created = Group.objects.get_or_create(name="Shop Employee")

        # Define the model and related models for which you want to assign permissions
        models = [Inventory]  # Add other related models as needed

        for model in models:
            content_type = ContentType.objects.get_for_model(model)

            # Assign create and edit permissions to the group for the model
            permission_create = Permission.objects.get(
                content_type=content_type, codename=f"add_{model._meta.model_name}" 
            )
            permission_create = Permission.objects.get(
                content_type=content_type, codename=f"change_{model._meta.model_name}" 
            )
            group.permissions.add(permission_create)

        # Save the group
        group.save()

# Create Shop Manager Group
@receiver(post_migrate)
def create_shop_manager_group(sender, **kwargs):
    if sender.label == "users":
        # Create the group
        group, created = Group.objects.get_or_create(name="Shop Manager")

        # Define the model and related models for which you want to assign permissions
        models = [Inventory, BaseItem, Location]  # Add other related models as needed

        for model in models:
            content_type = ContentType.objects.get_for_model(model)

            # Assign create and edit permissions to the group for the model
            permission_create = Permission.objects.get(
                content_type=content_type, codename=f"add_{model._meta.model_name}" 
            )
            permission_create = Permission.objects.get(
                content_type=content_type, codename=f"change_{model._meta.model_name}" 
            )
            group.permissions.add(permission_create)

        group.save()


# Default Locations
@receiver(post_migrate)
def create_default_building(sender, **kwargs):
    if sender.label == "users":
        apps = kwargs.get("apps")
        try:
            BuildingModel = apps.get_model("equipment", "Building")
        except Exception as e:
            print(f"Error retrieving Building model: {str(e)}")
            return

        # List of buildings to create
        buildings = [
            {"name": "Rowan Hall"},
            {"name": "Engineering Hall"},
        ]

        for building_data in buildings:
            name = building_data["name"]
            building, created = BuildingModel.objects.get_or_create(name=name)

            if created:
                # Building was newly created
                print(f'Building "{name}" created.')
            else:
                # Building already exists
                print(f'Building "{name}" already exists.')
