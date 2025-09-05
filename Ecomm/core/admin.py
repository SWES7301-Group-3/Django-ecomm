from django.contrib import admin
from .models import SiteSettings, ContactMessage, Newsletter, SystemStats

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'contact_email', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_tagline', 'contact_email', 'support_email', 'phone_number')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('Business Settings', {
            'fields': ('company_address', 'tax_rate', 'shipping_cost', 'free_shipping_threshold'),
            'classes': ('collapse',)
        }),
        ('Environmental Impact', {
            'fields': ('co2_reduction_per_gallon', 'total_gallons_processed', 'total_co2_saved'),
            'classes': ('collapse',)
        }),
        ('API Settings', {
            'fields': ('api_base_url', 'api_rate_limit'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'is_replied', 'created_at']
    list_filter = ['is_read', 'is_replied', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_as_read', 'mark_as_replied']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_replied(self, request, queryset):
        updated = queryset.update(is_replied=True)
        self.message_user(request, f'{updated} messages marked as replied.')
    mark_as_replied.short_description = 'Mark selected messages as replied'
    
@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'orders_today', 'revenue_today', 'active_subscriptions']
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        # Stats are automatically created
        return False

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscription_source', 'created_at']
    list_filter = ['is_active', 'subscription_source', 'created_at']  # is_active not active
    search_fields = ['email', 'name']
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriptions activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriptions deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'