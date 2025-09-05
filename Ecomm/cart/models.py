from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone
from products.models import Product


class Cart(models.Model):
    """
    Shopping cart. Can be linked to an authenticated user or kept by session_key for anonymous users.
    Use is_active=False for archived/converted carts (after order placement).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True,
        help_text="Optional: owner of the cart"
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        db_index=True,
        help_text="Session key for anonymous carts"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    metadata = models.JSONField(blank=True, null=True, help_text="Optional metadata (coupons, source, etc)")

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["session_key"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        if self.user:
            return f"Cart #{self.id} ({self.user})"
        return f"Cart #{self.id} (session={self.session_key})"

    def recalc_totals(self, save=True):
        """
        Recalculate subtotal and total from items.
        total currently equals subtotal - discounts + taxes + shipping.
        For now we just set total = subtotal (placeholders for tax/shipping).
        """
        agg = self.items.aggregate(
            subtotal=Sum(F("line_total"))
        )
        subtotal = agg["subtotal"] or Decimal("0.00")
        # Placeholder hooks for discount/tax/shipping calculation
        # discount = Decimal(self.metadata.get("discount_amount", "0.00")) if self.metadata else Decimal("0.00")
        # tax = compute_tax(subtotal - discount)
        # shipping = compute_shipping(...)
        total = subtotal
        self.subtotal = subtotal
        self.total = total
        if save:
            self.save(update_fields=["subtotal", "total", "updated_at"])
        return {"subtotal": subtotal, "total": total}

    @property
    def item_count(self):
        return self.items.aggregate(count=Sum("quantity"))["count"] or 0

    def add_product(self, product: Product, quantity: int = 1, replace_quantity: bool = False):
        """
        Convenience method to add a product to the cart.
        If replace_quantity is True, set to quantity; otherwise increment.
        Returns the CartItem instance.
        """
        item, created = CartItem.objects.get_or_create(cart=self, product=product, defaults={
            "quantity": 0,
            "unit_price": product.price,
        })
        if replace_quantity:
            item.quantity = quantity
        else:
            item.quantity = item.quantity + quantity
        item.unit_price = product.price  # snapshot current price
        item.save()
        return item

    def clear(self):
        """Remove all items from cart."""
        self.items.all().delete()
        self.recalc_totals()


class CartItem(models.Model):
    """
    Item inside a cart. unit_price and line_total are stored as snapshots so historical prices
    remain consistent if product price changes later.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(blank=True, null=True, help_text="Optional per-item metadata (config, options)")

    class Meta:
        ordering = ("-updated_at",)
        unique_together = ("cart", "product")
        indexes = [
            models.Index(fields=["cart", "product"]),
        ]

    def __str__(self):
        return f"{self.quantity}× {self.product.sku} in Cart #{self.cart_id}"

    def save(self, *args, **kwargs):
        # Ensure a sensible unit_price snapshot if not provided
        if not self.unit_price or Decimal(self.unit_price) == Decimal("0.00"):
            self.unit_price = self.product.price
        # Compute line total
        self.line_total = (Decimal(self.unit_price) * Decimal(self.quantity)).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
        # After saving the item, recalc the parent cart totals
        # Use update_fields=False for cart save inside recalc_totals to update timestamps
        try:
            self.cart.recalc_totals(save=True)
        except Exception:
            # Avoid raising from save to prevent blocking item save due to transient issues
            pass