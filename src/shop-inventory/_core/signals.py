# Define Required Permissions and Groups for the App to run after migration
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model


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
        users = [
            {"username": "admin", "password": "admin", "group": "Shop Manager"},
            {"username": "manager", "password": "manager", "group": "Shop Manager"},
            {"username": "employee", "password": "employee", "group": "Shop Employee"},
            {"username": "volunteer", "password": "volunteer", "group": "Shop Employee"},
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
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                print(f'User "{user.username}" added to group "{group.name}".')
            except Group.DoesNotExist:
                print(f'Group "{group_name}" does not exist.')
