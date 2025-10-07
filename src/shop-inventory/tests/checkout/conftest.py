"""Checkout app conftest.py for shop-inventory tests.

Contains fixtures specific to the checkout app.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission


@pytest.fixture
def staff_user():
    """Create a staff user with checkout-related permissions."""
    User = get_user_model()
    user = User.objects.create_user(
        username="staff",
        password="staffpass",
        is_staff=True,
    )
    # Add view_order permission
    view_order = Permission.objects.get(codename="view_order")
    user.user_permissions.add(view_order)
    return user
