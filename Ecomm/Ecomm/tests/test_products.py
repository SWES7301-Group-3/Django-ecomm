# Ecomm/tests/test_products.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_product_list_and_detail_views(client, product):
    list_url = reverse("products:product_list")
    r = client.get(list_url)
    assert r.status_code in (200, 302)

    detail_url = reverse("products:product_detail", kwargs={"pk": product.pk})
    r = client.get(detail_url)
    assert r.status_code in (200, 302)

@pytest.mark.django_db
def test_search_products(client, product):
    url = reverse("products:search_products")
    r = client.get(url, {"q": "BW-1000"})
    assert r.status_code in (200, 302)
