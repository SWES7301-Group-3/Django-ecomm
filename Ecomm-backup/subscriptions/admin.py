from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_month", "billing_cycle_days", "active")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "start_date")
    list_filter = ("status", "plan")