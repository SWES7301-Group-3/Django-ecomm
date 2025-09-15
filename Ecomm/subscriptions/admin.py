from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import SubscriptionPlan, UserSubscription, SubscriptionUsage, PaymentHistory

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'duration_days', 'price', 'api_rate_limit', 'is_active', 'created_at']
    list_filter = ['plan_type', 'duration_days', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['plan_type', 'duration_days', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'duration_days', 'price')
        }),
        ('Features', {
            'fields': ('api_rate_limit', 'features', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'plan_name', 'status', 'start_date', 'end_date', 'days_remaining_display', 'is_active']
    list_filter = ['status', 'is_active', 'plan__plan_type', 'auto_renew', 'payment_method', 'start_date']
    search_fields = ['user__username', 'user__email', 'plan__name', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at', 'days_remaining_display', 'is_expired_display']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan')
        }),
        ('Subscription Details', {
            'fields': ('start_date', 'end_date', 'status', 'is_active', 'auto_renew')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'stripe_subscription_id', 'stripe_customer_id')
        }),
        ('Cancellation', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Status Information', {
            'fields': ('days_remaining_display', 'is_expired_display'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def plan_name(self, obj):
        return obj.plan.name
    plan_name.short_description = 'Plan'
    plan_name.admin_order_field = 'plan__name'
    
    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days > 0:
            return format_html('<span style="color: green;">{} days</span>', days)
        else:
            return format_html('<span style="color: red;">Expired</span>')
    days_remaining_display.short_description = 'Days Remaining'
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Yes</span>')
        else:
            return format_html('<span style="color: green;">No</span>')
    is_expired_display.short_description = 'Expired'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')

@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = ['subscription_user', 'subscription_plan', 'date', 'api_calls', 'data_transferred_mb']
    list_filter = ['date', 'subscription__plan__plan_type']
    search_fields = ['subscription__user__username', 'subscription__plan__name']
    date_hierarchy = 'date'
    ordering = ['-date']
    readonly_fields = ['created_at']
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'
    subscription_user.admin_order_field = 'subscription__user__username'
    
    def subscription_plan(self, obj):
        return obj.subscription.plan.name
    subscription_plan.short_description = 'Plan'
    subscription_plan.admin_order_field = 'subscription__plan__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription__user', 'subscription__plan')

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['subscription_user', 'subscription_plan', 'amount', 'currency', 'status', 'payment_date']
    list_filter = ['status', 'currency', 'payment_date']
    search_fields = ['subscription__user__username', 'stripe_payment_intent_id']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    readonly_fields = ['payment_date']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('subscription', 'amount', 'currency', 'status')
        }),
        ('Stripe Details', {
            'fields': ('stripe_payment_intent_id',)
        }),
        ('Additional Information', {
            'fields': ('failure_reason', 'payment_date')
        }),
    )
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'
    subscription_user.admin_order_field = 'subscription__user__username'
    
    def subscription_plan(self, obj):
        return obj.subscription.plan.name
    subscription_plan.short_description = 'Plan'
    subscription_plan.admin_order_field = 'subscription__plan__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription__user', 'subscription__plan')

# Custom admin actions
def activate_subscriptions(modeladmin, request, queryset):
    queryset.update(is_active=True, status='active')
activate_subscriptions.short_description = "Activate selected subscriptions"

def deactivate_subscriptions(modeladmin, request, queryset):
    queryset.update(is_active=False, status='cancelled')
deactivate_subscriptions.short_description = "Deactivate selected subscriptions"

# Add actions to UserSubscriptionAdmin
UserSubscriptionAdmin.actions = [activate_subscriptions, deactivate_subscriptions]