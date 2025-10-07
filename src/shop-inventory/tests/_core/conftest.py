"""Core app conftest.py for shop-inventory tests.

Contains fixtures specific to the _core app (authentication, groups, etc.).
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


@pytest.fixture
def shop_employee_group():
    """Create or get the Shop Employee group."""
    group, _ = Group.objects.get_or_create(name="Shop Employee")
    return group


@pytest.fixture
def shop_manager_group():
    """Create or get the Shop Manager group."""
    group, _ = Group.objects.get_or_create(name="Shop Manager")
    return group


@pytest.fixture
def employee_user(shop_employee_group):
    """Create a user in the Shop Employee group."""
    User = get_user_model()
    user = User.objects.create_user(username="employee", password="employeepass")
    user.groups.add(shop_employee_group)
    return user
