# Ecomm/tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from django.apps import apps

@pytest.fixture
def User():
    return get_user_model()

@pytest.fixture
def user(db, User):
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="Passw0rd!123"
    )

@pytest.fixture
def client_logged(client, user):
    # your login view expects email + password
    client.post("/accounts/login/", {"email": "test@example.com", "password": "Passw0rd!123"})
    return client

@pytest.fixture
def category(db):
    ProductCategory = apps.get_model("products", "ProductCategory")
    return ProductCategory.objects.create(
        name="Units",
        description="Desalination units",
        slug="units" if hasattr(ProductCategory, "slug") else None,
        is_active=True
    )

@pytest.fixture
def product(db, category):
    """
    Create Product while only passing fields that actually exist on your model.
    Also supports either `product_category` or `category` FK names.
    """
    Product = apps.get_model("products", "Product")

    # collect concrete, editable field names
    field_names = {
        f.name for f in Product._meta.get_fields()
        if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False)
    }

    data = {}
    def set_if(name, value):
        if name in field_names and value is not None:
            data[name] = value

    # Common fields (guarded)
    set_if("name", "BW-1000")
    set_if("description", "BlueWave desalination unit")
    # FK name can be product_category or category
    if "product_category" in field_names:
        data["product_category"] = category
    elif "category" in field_names:
        data["category"] = category

    # price can be Decimal/Char/Integer in some repos — a simple string/number is fine
    set_if("price", "1999.99")
    set_if("product_type", "desalination_unit")
    set_if("is_active", True)
    set_if("stock_quantity", 50)
    # don't set slug unless it exists
    # set_if("slug", "bw-1000")

    return Product.objects.create(**data)
