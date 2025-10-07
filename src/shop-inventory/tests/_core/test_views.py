import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

pytestmark = pytest.mark.django_db


def test_index_view_unauthenticated(client):
    """Test index view for unauthenticated users"""
    response = client.get(reverse("index"))
    assert response.status_code == 200


def test_index_view_authenticated(client, user):
    """Test index view for authenticated users"""
    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.status_code == 200


def test_login_view_get(client):
    """Test login view GET request"""
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert "form" in response.context


def test_login_view_post_invalid(client):
    """Test login view with invalid credentials"""
    data = {"username": "invalid", "password": "invalid"}
    response = client.post(reverse("login"), data)
    assert response.status_code == 200
    assert "Invalid login credentials" in str(response.content)


def test_login_view_post_with_next(client, user):
    """Test login view with next parameter"""
    data = {"username": "testuser", "password": "testpass"}
    response = client.post(reverse("login") + "?next=/inventory/", data)
    assert response.status_code == 302


def test_logout_view(client, user):
    """Test logout view"""
    client.force_login(user)
    response = client.get(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("index")


def test_captive_portal_detect_automated(client):
    """Test captive portal detection for automated iOS check"""
    response = client.get(
        reverse("captive_detect"),
        HTTP_USER_AGENT="CaptiveNetworkSupport",
    )
    assert response.status_code == 200
    assert b"Success" in response.content


def test_captive_portal_detect_manual(client):
    """Test captive portal detection for manual navigation"""
    response = client.get(
        reverse("captive_detect"),
        HTTP_USER_AGENT="Mozilla/5.0",
    )
    assert response.status_code == 302
    assert response.url == reverse("index")


def test_group_required_decorator(client, employee_user):
    """Test group_required decorator allows access for group members"""
    client.force_login(employee_user)
    # Test with inventory index which requires Shop Employee group
    response = client.get(reverse("inventory:index"))
    assert response.status_code == 200


def test_group_required_decorator_superuser_access(client):
    """Test group_required decorator allows superuser access"""
    User = get_user_model()
    superuser = User.objects.create_superuser(username="admin", password="adminpass")
    client.force_login(superuser)
    # Test with inventory index which requires Shop Employee group
    response = client.get(reverse("inventory:index"))
    assert response.status_code == 200
