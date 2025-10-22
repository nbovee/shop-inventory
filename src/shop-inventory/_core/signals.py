# Define Required Permissions and Groups for the App to run after migration
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.conf import settings

# Default Locations
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User


# Create Shop Employee Group
@receiver(post_migrate)
def create_shop_employee_group(sender, **kwargs):
    if sender.label == "_core":
        # Create the group
        for group_name in ["Shop Manager", "Shop Employee"]:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                print(f'Group "{group.name}" created.')
            else:
                print(f'Group "{group.name}" already exists.')


# Create Default Users
@receiver(post_migrate)
def create_default_users(sender, **kwargs):
    if sender.label == "_core":
        User = get_user_model()
        # Define the default user data
        users = []
        admin_username = getattr(settings, "DJANGO_ADMIN_USERNAME")
        admin_password = getattr(settings, "DJANGO_ADMIN_PASSWORD")
        if admin_username and admin_password:
            users = [
                {
                    "username": admin_username,
                    "password": admin_password,
                    "is_superuser": True,
                    "is_staff": True,
                    "groups": ["Shop Manager", "Shop Employee"],
                },
            ]
        if settings.DEBUG:
            # Add default users for development environment
            users.extend(
                [
                    {
                        "username": "manager",
                        "password": "manager",
                        "groups": ["Shop Manager"],
                    },
                    {
                        "username": "employee",
                        "password": "employee",
                        "groups": ["Shop Employee"],
                    },
                ]
            )

        for user_data in users:
            username = user_data["username"]
            password = user_data["password"]
            groups = user_data.get("groups", [])
            is_superuser = user_data.get("is_superuser", False)

            # Check if the user already exists
            if User.objects.filter(username=username).exists():
                print(f'User "{username}" already exists.')
                continue

            # Create the user
            if is_superuser and password and username:
                user = User.objects.create_superuser(
                    username=username,
                    password=password,
                )
                print(f'Superuser "{user.username}" created successfully.')
            else:
                user = User.objects.create_user(username=username, password=password)
                print(f'User "{user.username}" created successfully.')

            # Add user to groups if specified
            for group_name in groups:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    print(f'User "{user.username}" added to group "{group.name}".')
                except Group.DoesNotExist:
                    print(f'Group "{group_name}" does not exist.')


# Add new users to Shop Employee group automatically
@receiver(post_save, sender=get_user_model())
def add_user_to_employee_group(sender, instance, created, **kwargs):
    """
    Signal handler to automatically add newly created users to the Shop Employee group.
    """
    if created:  # Only for newly created users, not updates
        try:
            employee_group = Group.objects.get(name="Shop Employee")
            instance.groups.add(employee_group)
            print(
                f'User "{instance.username}" automatically added to Shop Employee group.'
            )
        except Group.DoesNotExist:
            print('Group "Shop Employee" does not exist. User not added to any group.')


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
        models = [User]  # Add other related models as needed
        add_models_permissions(group, models, ["add", "change", "delete", "view"])
