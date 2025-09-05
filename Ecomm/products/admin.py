from django.contrib import admin
from .models import ProductCategory, Product, ProductImage, ProductReview, EnvironmentalImpactSnapshot

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):  # Changed from DesalinationUnitAdmin
    list_display = [
        'name', 
        'product_category',  # Changed from 'category'
        'price', 
        'product_type', 
        'capacity_gallons_per_day',  # Changed from 'capacity_m3_per_day'
        'stock_quantity', 
        'is_active', 
        'is_featured',
        'created_at'
    ]
    list_filter = [
        'product_type', 
        'product_category',  # Changed from 'category'
        'is_active', 
        'is_featured', 
        'energy_source',
        'created_at'
    ]
    search_fields = ['name', 'description']  # Removed 'sku' since it doesn't exist
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline]
    # Removed prepopulated_fields for 'slug' since Product model doesn't have slug field
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'product_category', 'price', 'product_type')
        }),
        ('Technical Specifications', {
            'fields': (
                'capacity_gallons_per_day', 
                'power_consumption_watts', 
                'dimensions', 
                'weight_pounds'
            ),
            'classes': ('collapse',)
        }),
        ('Environmental Impact', {
            'fields': ('co2_savings_per_year', 'energy_source'),
            'classes': ('collapse',)
        }),
        ('Inventory & Status', {
            'fields': ('stock_quantity', 'is_active', 'is_featured')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_featured', 'remove_featured', 'activate_products', 'deactivate_products']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products marked as featured.')
    make_featured.short_description = 'Mark selected products as featured'
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} products removed from featured.')
    remove_featured.short_description = 'Remove from featured'
    
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products activated.')
    activate_products.short_description = 'Activate selected products'
    
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products deactivated.')
    deactivate_products.short_description = 'Deactivate selected products'

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'title', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'review_text']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(EnvironmentalImpactSnapshot)
class EnvironmentalImpactSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'product', 
        'recorded_at', 
        'energy_kwh_per_m3', 
        'co2_kg_per_m3',
        'water_recovery_rate'
    ]
    list_filter = ['recorded_at']
    search_fields = ['product__name', 'notes']
    readonly_fields = ['recorded_at']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'recorded_at')
        }),
        ('Environmental Metrics', {
            'fields': (
                'energy_kwh_per_m3',
                'co2_kg_per_m3', 
                'brine_disposal_score',
                'water_recovery_rate',
                'membrane_efficiency'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        })
    )