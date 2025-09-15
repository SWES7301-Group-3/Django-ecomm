from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('basic_user', 'Basic User'),
        ('researcher', 'Researcher'),
        ('premium', 'Premium'),
    ]
    
    DURATION_CHOICES = [
        (30, '30 Days'),
        (90, '90 Days'),
        (365, '365 Days'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    duration_days = models.IntegerField(choices=DURATION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    api_rate_limit = models.IntegerField(default=1000, help_text="API requests per hour")
    description = models.TextField(blank=True)
    features = models.JSONField(default=list, blank=True, help_text="List of plan features")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['plan_type', 'duration_days']
        ordering = ['price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
    
    def clean(self):
        if self.price < 0:
            raise ValidationError('Price cannot be negative')
        if self.api_rate_limit < 0:
            raise ValidationError('API rate limit cannot be negative')
    
    def __str__(self):
        return f"{self.name} - {self.duration_days} days (${self.price})"

class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    
    # This now correctly references your custom user model
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default='stripe')
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['end_date']),
            models.Index(fields=['stripe_subscription_id']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        
        # Update status based on conditions
        if self.is_expired and self.status == 'active':
            self.status = 'expired'
        elif not self.is_active and self.status == 'active':
            self.status = 'cancelled'
            if not self.cancelled_at:
                self.cancelled_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.end_date
    
    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now()).days
    
    @property
    def is_valid(self):
        return self.is_active and not self.is_expired and self.status == 'active'
    
    def cancel(self, reason=""):
        """Cancel the subscription"""
        self.is_active = False
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()
    
    def renew(self, new_plan=None):
        """Renew the subscription"""
        plan = new_plan or self.plan
        new_end_date = self.end_date + timedelta(days=plan.duration_days)
        
        # Create new subscription
        return UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            start_date=self.end_date,
            end_date=new_end_date,
            auto_renew=self.auto_renew,
            payment_method=self.payment_method
        )
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

class SubscriptionUsage(models.Model):
    """Track API usage for subscriptions"""
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='usage_records')
    date = models.DateField(default=timezone.now)
    api_calls = models.IntegerField(default=0)
    data_transferred_mb = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['subscription', 'date']
        ordering = ['-date']
        verbose_name = 'Subscription Usage'
        verbose_name_plural = 'Subscription Usage Records'
    
    def __str__(self):
        return f"{self.subscription.user.username} - {self.date} ({self.api_calls} calls)"

class PaymentHistory(models.Model):
    """Track payment history"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    failure_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment History'
        verbose_name_plural = 'Payment History'
    
    def __str__(self):
        return f"{self.subscription.user.username} - ${self.amount} ({self.status})"