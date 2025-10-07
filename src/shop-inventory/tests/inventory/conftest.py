"""Inventory app conftest.py for shop-inventory tests.

Contains fixtures specific to the inventory app.
"""

import pytest


@pytest.fixture
def inactive_location():
    """Create an inactive location for testing."""
    from inventory.models import Location

    location = Location.objects.create(name="Inactive Location")
    location.active = False
    location.save()
    return location
