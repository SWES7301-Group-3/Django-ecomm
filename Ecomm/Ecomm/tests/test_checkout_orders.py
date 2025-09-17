# Ecomm/tests/test_checkout_orders.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_checkout_page_loads(client_logged):
    url = reverse("cart:checkout")
    r = client_logged.get(url)
    assert r.status_code in (200, 302)

@pytest.mark.django_db
def test_order_history_requires_login_redirects(client):
    url = reverse("orders:order_history")
    r = client.get(url)
    assert r.status_code in (301, 302)
    assert "/accounts/login" in r.headers.get("Location", "")
