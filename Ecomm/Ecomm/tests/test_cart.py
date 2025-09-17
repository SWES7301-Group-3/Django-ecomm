# Ecomm/tests/test_cart.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_add_update_remove_cart_item(client_logged, product):
    # lazy import of models AFTER Django is set up
    from cart.models import Cart, CartItem

    # add to cart
    add_url = reverse("cart:add_to_cart", kwargs={"product_id": product.id})
    r = client_logged.post(add_url, {"quantity": 2})
    assert r.status_code in (200, 302)

    # cart detail
    detail_url = reverse("cart:cart_detail")
    r = client_logged.get(detail_url)
    assert r.status_code == 200

    # verify DB state
    cart = Cart.objects.get(user__email="test@example.com")
    item = CartItem.objects.get(cart=cart, product=product)
    assert item.quantity == 2

    # update quantity
    update_url = reverse("cart:update_cart_item", kwargs={"item_id": item.id})
    r = client_logged.post(update_url, {"quantity": 5})
    assert r.status_code in (200, 302)
    item.refresh_from_db()
    assert item.quantity == 5

    # remove item
    remove_url = reverse("cart:remove_from_cart", kwargs={"item_id": item.id})
    r = client_logged.post(remove_url)
    assert r.status_code in (200, 302)
    assert not CartItem.objects.filter(id=item.id).exists()

@pytest.mark.django_db
def test_clear_cart(client_logged, product):
    from cart.models import Cart, CartItem  # lazy import

    add_url = reverse("cart:add_to_cart", kwargs={"product_id": product.id})
    client_logged.post(add_url, {"quantity": 1})

    clear_url = reverse("cart:clear_cart")
    r = client_logged.post(clear_url)
    assert r.status_code in (200, 302)

    cart = Cart.objects.get(user__email="test@example.com")
    assert CartItem.objects.filter(cart=cart).count() == 0
