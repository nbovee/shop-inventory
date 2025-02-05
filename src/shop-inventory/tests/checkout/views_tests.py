import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from inventory.models import InventoryEntry, Product, Location
from checkout.views import get_cart
from checkout.models import Order


@pytest.fixture
def base_item():
    return Product.objects.create(name="Test Item", manufacturer="Test Manufacturer")


@pytest.fixture
def location():
    return Location.objects.get_or_create(name="Shop Floor")[0]


@pytest.fixture
def inventory_item(base_item, location):
    return InventoryEntry.objects.create(
        base_item=base_item, location=location, quantity=10
    )


@pytest.fixture
def cart_session():
    return {"1": 2}  # Item ID 1, quantity 2


@pytest.mark.django_db
class TestCheckoutViews:
    def test_index_get(self, client, inventory_item):
        url = reverse("checkout:index")
        response = client.get(url)
        assert response.status_code == 200
        assert list(response.context["inventory_items"]) == [inventory_item]

    def test_index_get_with_filter(self, client, inventory_item):
        url = reverse("checkout:index")
        response = client.get(url, {"filter": "Test"})
        assert response.status_code == 200
        assert list(response.context["inventory_items"]) == [inventory_item]

        response = client.get(url, {"filter": "NonExistent"})
        assert response.status_code == 200
        assert list(response.context["inventory_items"]) == []

    def test_index_post_valid(self, client, inventory_item):
        url = reverse("checkout:index")
        response = client.post(url, {"product_id": inventory_item.id, "quantity": 1})
        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Item added to cart." in str(messages[0])

    def test_index_post_invalid_quantity(self, client, inventory_item):
        url = reverse("checkout:index")
        response = client.post(
            url,
            {
                "product_id": inventory_item.id,
                "quantity": 999,  # More than available
            },
        )
        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Item added to cart." not in str(messages[0])

    def test_get_cart(self, rf, cart_session):
        request = rf.get("/")
        request.session = {"cart": cart_session}
        cart = get_cart(request)
        assert cart == cart_session

    def test_process_order_valid(self, client, cart_session, inventory_item):
        session = client.session
        session["cart"] = cart_session
        session.save()

        url = reverse("checkout:process_order")
        response = client.post(url, {"implicit_id": "123456789123"})

        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "processed successfully" in str(messages[0])

        # Verify cart was cleared
        assert "cart" not in client.session

        # Verify order was created
        assert Order.objects.count() == 1
        order = Order.objects.first()
        assert order.implicit_id == "123456789123"

    def test_process_order_invalid(self, client, cart_session):
        session = client.session
        session["cart"] = cart_session
        session.save()

        url = reverse("checkout:process_order")
        response = client.post(
            url,
            {
                "payment_method": "INVALID",
                "implicit_id": "",  # Required field
            },
        )

        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) >= 1
        assert any("error" in str(msg).lower() for msg in messages)

        # Verify cart was not cleared
        assert client.session["cart"] == cart_session
