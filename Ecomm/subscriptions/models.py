from django.db import models
from django.conf import settings

class SubscriptionPlan(models.Model):
    """
    API subscription plan model.
    Reusable subscription plan that can be later linked to a payment provider (stripe_plan_id).
    """
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    price_per_month = models.DecimalField(max_digits=9, decimal_places=2)
    billing_cycle_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)
    features = models.JSONField(blank=True, null=True, help_text="List or map of features included")
    active = models.BooleanField(default=True)
    external_plan_id = models.CharField(max_length=255, blank=True, help_text="Plan id on payment gateway")

    class Meta:
        ordering = ("price_per_month",)

    def __str__(self):
        return f"{self.name} - ${self.price_per_month}/mo"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="trial")
    start_date = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    external_subscription_id = models.CharField(max_length=255, blank=True, help_text="ID in payment gateway")
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ("-start_date",)
        unique_together = ("user", "plan")

    def __str__(self):
        return f"{self.user} => {self.plan.name} ({self.status})"