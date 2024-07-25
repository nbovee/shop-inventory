# Define Required Permissions and Groups for the App to run after migration
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Inventory, BaseItem, Location
from django.contrib.auth.models import User


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


# Create Default Users
@receiver(post_migrate)
def create_default_users(sender, **kwargs):
    if sender.label == "users":

        # Define the default user data
        users = [
            {"username": "manager", "password": "manager", "group": "Shop Manager"},
            {"username": "employee", "password": "employee", "group": "Shop Employee"},

        ]

        for user_data in users:
            username = user_data["username"]
            password = user_data["password"]
            group_name = user_data["group"]

            # Check if the user already exists
            if User.objects.filter(username=username).exists():
                print(f'User "{username}" already exists.')
                continue

            # Create the user
            user = User.objects.create_user(username=username, password=password)

            # Add the user to the specified group
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                print(f'User "{username}" added to group "{group_name}".')
            except Group.DoesNotExist:
                print(f'Group "{group_name}" does not exist.')

        print("Default users created.")
