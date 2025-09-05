from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    PRODUCT_TYPES = [
        ('desalination_unit', 'Desalination Unit'),
        ('accessory', 'Accessory'),
        ('replacement_part', 'Replacement Part'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    product_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='desalination_unit')
    
    # Technical specifications
    capacity_gallons_per_day = models.IntegerField(null=True, blank=True, help_text="Water production capacity per day")
    power_consumption_watts = models.IntegerField(null=True, blank=True, help_text="Power consumption in watts")
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H in inches")
    weight_pounds = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Environmental impact (adding these back since they're used in environmental_score)
    co2_savings_per_year = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="CO2 savings in kg per year")
    energy_source = models.CharField(max_length=50, default="Solar", help_text="Primary energy source")
    
    # Inventory and status
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Media
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'pk': self.pk})
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    @property
    def environmental_score(self):
        """Calculate environmental impact score (0-100)"""
        score = 0
        if self.co2_savings_per_year:
            score += min(int(self.co2_savings_per_year / 10), 50)  # Max 50 points for CO2 savings
        if self.energy_source and self.energy_source.lower() == 'solar':
            score += 30  # 30 points for solar power
        if self.capacity_gallons_per_day:
            score += min(int(self.capacity_gallons_per_day / 100), 20)  # Max 20 points for capacity
        return min(score, 100)
    
    @property
    def daily_co2_savings(self):
        """Calculate daily CO2 savings in kg"""
        if self.co2_savings_per_year:
            return round(float(self.co2_savings_per_year) / 365, 2)
        return 0
    
    @property
    def efficiency_rating(self):
        """Calculate efficiency rating based on power consumption vs capacity"""
        if self.power_consumption_watts and self.capacity_gallons_per_day:
            # Lower watts per gallon = better efficiency
            watts_per_gallon = self.power_consumption_watts / self.capacity_gallons_per_day
            if watts_per_gallon < 10:
                return "Excellent"
            elif watts_per_gallon < 20:
                return "Good"
            elif watts_per_gallon < 30:
                return "Fair"
            else:
                return "Poor"
        return "Not Available"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - Image"

class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    review_text = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"

class EnvironmentalImpactSnapshot(models.Model):
    """
    Optional historical/environmental snapshots per product for tracking improvements,
    lifecycle assessments, or per-configuration metrics.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="impact_snapshots")
    recorded_at = models.DateTimeField(auto_now_add=True)
    energy_kwh_per_m3 = models.FloatField(null=True, blank=True, help_text="Energy consumption in kWh per cubic meter")
    co2_kg_per_m3 = models.FloatField(null=True, blank=True, help_text="CO2 emissions in kg per cubic meter")
    brine_disposal_score = models.FloatField(null=True, blank=True, help_text="Normalized impact score for brine disposal (0-100)")
    water_recovery_rate = models.FloatField(null=True, blank=True, help_text="Percentage of input water recovered as fresh water")
    membrane_efficiency = models.FloatField(null=True, blank=True, help_text="Membrane efficiency percentage")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-recorded_at",)

    def __str__(self):
        return f"{self.product.name} impact snapshot @ {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"