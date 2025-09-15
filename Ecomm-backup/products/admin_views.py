from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.text import slugify
from django.conf import settings
import csv
import io
from .models import Product, ProductCategory, ProductImage
from .forms import ProductUploadForm, BulkProductUploadForm, ProductCategoryForm, ProductImageUploadForm

@staff_member_required
def admin_product_upload(request):
    """Admin page for uploading products"""
    
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        image_form = ProductImageUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Save the product
            product = form.save()
            
            # Handle additional images if provided
            if image_form.is_valid():
                images = image_form.cleaned_data.get('images', [])
                if not isinstance(images, list):
                    images = [images] if images else []
                
                for i, image in enumerate(images):
                    if image:
                        ProductImage.objects.create(
                            product=product,
                            image=image,
                            alt_text=f"{product.name} - Image {i+1}",
                            is_primary=(i == 0 and not product.image)  # First image is primary if no main image
                        )
            
            messages.success(request, f'Product "{product.name}" uploaded successfully!')
            
            # Check if user wants to add another product
            if 'add_another' in request.POST:
                return redirect('products:admin_product_upload')
            else:
                return redirect('products:admin_product_list')
    else:
        form = ProductUploadForm()
        image_form = ProductImageUploadForm()
    
    # Get recent products for reference
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    # Get categories
    categories = ProductCategory.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'image_form': image_form,
        'recent_products': recent_products,
        'categories': categories,
        'page_title': 'Upload New Product',
        'section': 'products'
    }
    return render(request, 'products/admin/upload_product.html', context)

@staff_member_required
def admin_product_list(request):
    """Admin page for managing products"""
    
    # Search and filter
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    products = Product.objects.select_related('product_category').order_by('-created_at')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(product_category_id=category_filter)
    
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    elif status_filter == 'featured':
        products = products.filter(is_featured=True)
    elif status_filter == 'out_of_stock':
        products = products.filter(stock_quantity=0)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(is_active=True).count(),
        'featured_products': Product.objects.filter(is_featured=True).count(),
        'out_of_stock': Product.objects.filter(stock_quantity=0).count(),
    }
    
    categories = ProductCategory.objects.filter(is_active=True)
    
    context = {
        'products': products_page,
        'categories': categories,
        'stats': stats,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'page_title': 'Manage Products',
        'section': 'products'
    }
    return render(request, 'products/admin/product_list.html', context)

@staff_member_required
def admin_bulk_upload(request):
    """Admin page for bulk product upload"""
    
    if request.method == 'POST':
        form = BulkProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            
            try:
                # Read CSV file
                decoded_file = csv_file.read().decode('utf-8')
                csv_data = csv.DictReader(io.StringIO(decoded_file))
                
                success_count = 0
                error_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_data, start=2):
                    try:
                        # Get or create category
                        category_name = row.get('category', '').strip()
                        if category_name:
                            category, _ = ProductCategory.objects.get_or_create(
                                name=category_name,
                                defaults={
                                    'slug': slugify(category_name),
                                    'is_active': True
                                }
                            )
                        else:
                            category = None
                        
                        # Create product
                        product = Product.objects.create(
                            name=row.get('name', '').strip(),
                            description=row.get('description', '').strip(),
                            product_category=category,
                            price=float(row.get('price', 0)),
                            product_type=row.get('product_type', 'desalination_unit'),
                            capacity_gallons_per_day=int(row.get('capacity_gallons_per_day', 0)) if row.get('capacity_gallons_per_day') else None,
                            power_consumption_watts=int(row.get('power_consumption_watts', 0)) if row.get('power_consumption_watts') else None,
                            dimensions=row.get('dimensions', '').strip(),
                            weight_pounds=float(row.get('weight_pounds', 0)) if row.get('weight_pounds') else None,
                            co2_savings_per_year=float(row.get('co2_savings_per_year', 0)) if row.get('co2_savings_per_year') else None,
                            energy_source=row.get('energy_source', 'Solar').strip(),
                            stock_quantity=int(row.get('stock_quantity', 0)),
                            is_active=row.get('is_active', '').lower() in ['true', '1', 'yes'],
                            is_featured=row.get('is_featured', '').lower() in ['true', '1', 'yes'],
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                
                if success_count > 0:
                    messages.success(request, f'Successfully uploaded {success_count} products!')
                
                if error_count > 0:
                    error_message = f'{error_count} products failed to upload:\n' + '\n'.join(errors[:5])
                    if len(errors) > 5:
                        error_message += f'\n... and {len(errors) - 5} more errors'
                    messages.error(request, error_message)
                
                return redirect('products:admin_product_list')
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
    else:
        form = BulkProductUploadForm()
    
    context = {
        'form': form,
        'page_title': 'Bulk Product Upload',
        'section': 'products'
    }
    return render(request, 'products/admin/bulk_upload.html', context)

@staff_member_required
def admin_product_edit(request, product_id):
    """Edit product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES, instance=product)
        image_form = ProductImageUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            product = form.save()
            
            # Handle new images
            if image_form.is_valid():
                images = image_form.cleaned_data.get('images', [])
                if not isinstance(images, list):
                    images = [images] if images else []
                
                for image in images:
                    if image:
                        ProductImage.objects.create(
                            product=product,
                            image=image,
                            alt_text=f"{product.name} - Image",
                            is_primary=False
                        )
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('products:admin_product_list')
    else:
        form = ProductUploadForm(instance=product)
        image_form = ProductImageUploadForm()
    
    # Get existing images
    existing_images = ProductImage.objects.filter(product=product)
    
    context = {
        'form': form,
        'image_form': image_form,
        'product': product,
        'existing_images': existing_images,
        'page_title': f'Edit Product: {product.name}',
        'section': 'products'
    }
    return render(request, 'products/admin/edit_product.html', context)

@staff_member_required
def admin_delete_product(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('products:admin_product_list')
    
    context = {
        'product': product,
        'page_title': f'Delete Product: {product.name}',
        'section': 'products'
    }
    return render(request, 'products/admin/delete_product.html', context)

@staff_member_required
def admin_category_management(request):
    """Manage product categories"""
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            if not category.slug:
                category.slug = slugify(category.name)
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('products:admin_category_management')
    else:
        form = ProductCategoryForm()
    
    categories = ProductCategory.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    context = {
        'form': form,
        'categories': categories,
        'page_title': 'Manage Categories',
        'section': 'products'
    }
    return render(request, 'products/admin/category_management.html', context)

@staff_member_required
def download_csv_template(request):
    """Download CSV template for bulk upload"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="product_upload_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'name', 'description', 'category', 'price', 'product_type',
        'capacity_gallons_per_day', 'power_consumption_watts', 'dimensions',
        'weight_pounds', 'co2_savings_per_year', 'energy_source',
        'stock_quantity', 'is_active', 'is_featured'
    ])
    
    # Add sample data
    writer.writerow([
        'AquaPure 1000', 
        'Compact solar-powered desalination unit for residential use',
        'Residential',
        '2999.99',
        'desalination_unit',
        '1000',
        '250',
        '24 x 18 x 30',
        '85.5',
        '450.00',
        'Solar',
        '10',
        'true',
        'false'
    ])
    
    return response

@staff_member_required
def delete_product_image(request, image_id):
    """Delete a product image"""
    if request.method == 'POST':
        image = get_object_or_404(ProductImage, id=image_id)
        product_id = image.product.id
        image.delete()
        messages.success(request, 'Image deleted successfully!')
        return redirect('products:admin_product_edit', product_id=product_id)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)