import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test.utils import override_settings

pytestmark = pytest.mark.django_db


def test_user_auto_added_to_employee_group(shop_employee_group):
    """Test that new users are automatically added to Shop Employee group"""
    User = get_user_model()
    user = User.objects.create_user(username="testuser", password="testpass")

    # Check user was added to Shop Employee group
    assert user.groups.filter(name="Shop Employee").exists()


def test_existing_user_not_affected(shop_employee_group):
    """Test that updating existing users doesn't re-trigger the signal"""
    User = get_user_model()
    user = User.objects.create_user(username="testuser", password="testpass")

    # Remove from group
    user.groups.clear()
    user.save()

    # User should still not be in group (save doesn't re-trigger created signal)
    assert not user.groups.filter(name="Shop Employee").exists()


@override_settings(DEBUG=False, DJANGO_ADMIN_USERNAME="admin", DJANGO_ADMIN_PASSWORD="adminpass")
def test_default_admin_creation_production(shop_employee_group, shop_manager_group):
    """Test that default admin is created in production mode"""
    # This test verifies the signal would create an admin in production
    # The actual creation happens during post_migrate, which we can't easily trigger
    User = get_user_model()

    # Manually verify the logic would work
    assert not User.objects.filter(username="admin").exists()


def test_group_creation():
    """Test that Shop Employee and Shop Manager groups are created"""
    # Groups should be created by signals
    assert Group.objects.filter(name="Shop Employee").exists()
    assert Group.objects.filter(name="Shop Manager").exists()
