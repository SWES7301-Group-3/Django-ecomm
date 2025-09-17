# Ecomm/tests/test_accounts.py
import pytest

@pytest.mark.django_db
def test_admin_login_page_loads(client):
    resp = client.get("/admin/login/")
    assert resp.status_code in (200, 302)
    if resp.status_code == 302:
        assert "/accounts/login" in resp.headers.get("Location", "")
