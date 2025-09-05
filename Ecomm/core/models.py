from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class TimeStampedModel(models.Model):
    """Abstract base class with timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SiteSettings(models.Model):
    """Global site settings"""
    site_name = models.CharField(max_length=100, default="BlueWave Solutions")
    site_tagline = models.CharField(max_length=200, default="Sustainable Water Solutions for a Better Tomorrow")
    contact_email = models.EmailField(default="contact@bluewave-solutions.com")
    support_email = models.EmailField(default="support@bluewave-solutions.com")
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Social media links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # Business settings
    company_address = models.TextField(blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0875, help_text="Default tax rate (e.g., 0.0875 for 8.75%)")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=25.00, help_text="Default shipping cost")
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, help_text="Free shipping above this amount")
    
    # Environmental impact settings
    co2_reduction_per_gallon = models.DecimalField(max_digits=8, decimal_places=4, default=2.3, help_text="CO2 reduction in kg per gallon processed")
    total_gallons_processed = models.BigIntegerField(default=0, help_text="Total gallons processed by all units")
    total_co2_saved = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total CO2 saved in kg")
    
    # API settings
    api_base_url = models.URLField(default="https://api.bluewave-solutions.com/v1/")
    api_rate_limit = models.IntegerField(default=1000, help_text="API calls per hour")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError('Only one SiteSettings instance is allowed')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create site settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class Newsletter(TimeStampedModel):
    """Newsletter subscription model"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscription_source = models.CharField(max_length=50, default='website')
    
    def __str__(self):
        return self.email

class ContactMessage(TimeStampedModel):
    """Contact form submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"

class SystemStats(TimeStampedModel):
    """System statistics and metrics"""
    date = models.DateField(default=timezone.now)
    
    # User metrics
    total_users = models.IntegerField(default=0)
    new_users_today = models.IntegerField(default=0)
    active_users_today = models.IntegerField(default=0)
    
    # Sales metrics
    total_orders = models.IntegerField(default=0)
    orders_today = models.IntegerField(default=0)
    revenue_today = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Product metrics
    products_sold_today = models.IntegerField(default=0)
    total_products_sold = models.IntegerField(default=0)
    
    # Subscription metrics
    active_subscriptions = models.IntegerField(default=0)
    new_subscriptions_today = models.IntegerField(default=0)
    subscription_revenue_today = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Environmental metrics
    gallons_processed_today = models.IntegerField(default=0)
    co2_saved_today = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        verbose_name = "System Stats"
        verbose_name_plural = "System Stats"
    
    def __str__(self):
        return f"Stats for {self.date}"
    
    @classmethod
    def get_today_stats(cls):
        """Get or create today's stats"""
        today = timezone.now().date()
        stats, created = cls.objects.get_or_create(date=today)
        return stats
    

class Newsletter(TimeStampedModel):
    """Newsletter subscription model"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)  # Make sure this is is_active, not active
    subscription_source = models.CharField(max_length=50, default='website')
    
    def __str__(self):
        return self.email