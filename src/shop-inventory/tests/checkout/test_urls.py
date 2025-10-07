# Create your tests here.
import pytest
from django.urls import reverse, resolve

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


def test_checkout_index():
    """Test the checkout index URL pattern"""
    url = reverse("checkout:index")
    assert url == "/checkout/"
    resolver = resolve("/checkout/")
    assert resolver.url_name == "index"
    assert resolver.namespace == "checkout"


def test_checkout_process_order():
    """Test the checkout process_order URL pattern"""
    url = reverse("checkout:process_order")
    assert url == "/checkout/process/"
    resolver = resolve("/checkout/process/")
    assert resolver.url_name == "process_order"
    assert resolver.namespace == "checkout"
