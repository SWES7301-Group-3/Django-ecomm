from django import forms
from django.core.exceptions import ValidationError
from .models import Product, ProductCategory, ProductImage
import json

class ProductUploadForm(forms.ModelForm):
    """Form for uploading/creating products"""
    
    # Additional fields for easier input
    features_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4, 
            'class': 'form-control',
            'placeholder': 'Enter features separated by commas\nExample: Solar powered, IoT enabled, Remote monitoring'
        }),
        required=False,
        help_text="Enter product features separated by commas"
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'product_category', 'price', 'product_type',
            'capacity_gallons_per_day', 'power_consumption_watts', 'dimensions', 
            'weight_pounds', 'co2_savings_per_year', 'energy_source',
            'stock_quantity', 'is_active', 'is_featured', 'image'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detailed product description...'
            }),
            'product_category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity_gallons_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'power_consumption_watts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'L x W x H (inches)'
            }),
            'weight_pounds': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0'
            }),
            'co2_savings_per_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'energy_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Solar, Wind, Hybrid'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise ValidationError("Price must be greater than 0")
        return price
    
    def clean_stock_quantity(self):
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise ValidationError("Stock quantity cannot be negative")
        return stock


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Custom field for multiple file uploads"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ProductImageUploadForm(forms.Form):
    """Separate form for uploading product images"""
    images = MultipleFileField(
        required=False,
        help_text="Select multiple product images (JPG, PNG, WebP, max 5MB each)"
    )
    
    def clean_images(self):
        images = self.cleaned_data.get('images', [])
        if not isinstance(images, list):
            images = [images] if images else []
        
        for image in images:
            if image:
                # Check file size (max 5MB)
                if image.size > 5 * 1024 * 1024:
                    raise ValidationError(f"Image {image.name} is too large. Maximum size is 5MB.")
                
                # Check file type
                allowed_types = ['image/jpeg', 'image/png', 'image/webp']
                if image.content_type not in allowed_types:
                    raise ValidationError(f"Image {image.name} must be JPG, PNG, or WebP format.")
        
        return images


class BulkProductUploadForm(forms.Form):
    """Form for bulk product upload via CSV"""
    
    csv_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload a CSV file with product data"
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise ValidationError("File must be a CSV file")
            
            # Check file size (max 10MB)
            if csv_file.size > 10 * 1024 * 1024:
                raise ValidationError("CSV file is too large. Maximum size is 10MB.")
        
        return csv_file


class ProductCategoryForm(forms.ModelForm):
    """Form for creating product categories"""
    
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'slug', 'is_active']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description...'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'category-slug (auto-generated if empty)'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }