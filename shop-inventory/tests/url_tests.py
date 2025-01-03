import pytest
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="testpass123")


def test_core_index():
    """Test the index URL pattern"""
    url = reverse("index")
    assert url == "/"
    resolver = resolve("/")
    assert resolver.view_name == "index"


def test_inventory_index():
    """Test the inventory URL pattern"""
    url = reverse("inventory:index")  # Assuming 'index' is the name in inventory.urls
    assert url == "/inventory/"
    resolver = resolve("/inventory/")
    assert resolver.url_name == "index"
    assert resolver.namespace == "inventory"


def test_checkout_index():
    """Test the checkout URL pattern"""
    url = reverse("checkout:index")  # Assuming 'index' is the name in checkout.urls
    assert url == "/checkout/"
    resolver = resolve("/checkout/")
    assert resolver.url_name == "index"
    assert resolver.namespace == "checkout"


def test_login_url():
    """Test the login URL pattern"""
    url = reverse("login")
    assert url == "/login/"
    resolver = resolve("/login/")
    assert resolver.view_name == "login"


def test_logout_url():
    """Test the logout URL pattern"""
    url = reverse("logout")
    assert url == "/logout/"
    resolver = resolve("/logout/")
    assert resolver.view_name == "logout"


@pytest.mark.django_db
def test_login_view_get(client):
    """Test the login view GET request"""
    response = client.get(reverse("login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_view_post_success(client, user):
    """Test successful login"""
    response = client.post(
        reverse("login"), {"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 302  # Redirect after successful login


@pytest.mark.django_db
def test_logout_view(client, user):
    """Test logout functionality"""
    # First login
    client.login(username="testuser", password="testpass123")
    # Then test logout
    response = client.get(reverse("logout"))
    assert response.status_code == 302  # Redirect after logout
