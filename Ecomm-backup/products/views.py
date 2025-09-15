from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from .models import Product, ProductCategory, ProductReview
from cart.models import Cart, CartItem

def product_list(request):
    """
    Product listing with filtering and search
    """
    products = Product.objects.filter(is_active=True).select_related('product_category')
    categories = ProductCategory.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(product_category__name__icontains=search_query)
        )
    
    # Category filtering
    current_category = request.GET.get('category', '')
    if current_category:
        try:
            current_category = int(current_category)
            products = products.filter(product_category_id=current_category)
        except (ValueError, TypeError):
            current_category = ''
    
    # Sorting
    current_sort = request.GET.get('sort', 'name')
    if current_sort == 'price_low':
        products = products.order_by('price')
    elif current_sort == 'price_high':
        products = products.order_by('-price')
    elif current_sort == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'current_category': current_category,
        'current_sort': current_sort,
        'page_title': 'Products - BlueWave Solutions',
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):  # Changed parameter name to match URL
    """
    Product detail view
    """
    product = get_object_or_404(
        Product.objects.select_related('product_category').prefetch_related('reviews', 'images'), 
        pk=pk,  # Changed to pk
        is_active=True
    )
    
    # Get related products from the same category
    related_products = Product.objects.filter(
        product_category=product.product_category,
        is_active=True
    ).exclude(pk=product.pk)[:4]  # Changed to pk
    
    # Get product reviews
    reviews = product.reviews.all().select_related('user')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if user has this item in cart
    in_cart = False
    cart_quantity = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.filter(cart=cart, product=product).first()
            if cart_item:
                in_cart = True
                cart_quantity = cart_item.quantity
        except Cart.DoesNotExist:
            pass
    
    # Product specifications for display
    specifications = []
    if product.capacity_gallons_per_day:
        specifications.append({
            'name': 'Daily Capacity',
            'value': f'{product.capacity_gallons_per_day:,} gallons/day',
            'icon': 'fas fa-tint'
        })
    if product.power_consumption_watts:
        specifications.append({
            'name': 'Power Consumption', 
            'value': f'{product.power_consumption_watts} watts',
            'icon': 'fas fa-bolt'
        })
    if product.energy_source:
        specifications.append({
            'name': 'Energy Source',
            'value': product.energy_source,
            'icon': 'fas fa-solar-panel'
        })
    if product.daily_co2_savings:
        specifications.append({
            'name': 'Daily CO₂ Savings',
            'value': f'{product.daily_co2_savings} kg/day',
            'icon': 'fas fa-seedling'
        })
    if product.dimensions:
        specifications.append({
            'name': 'Dimensions',
            'value': product.dimensions,
            'icon': 'fas fa-ruler'
        })
    if product.weight_pounds:
        specifications.append({
            'name': 'Weight',
            'value': f'{product.weight_pounds} lbs',
            'icon': 'fas fa-weight'
        })
    if product.efficiency_rating != "Not Available":
        specifications.append({
            'name': 'Efficiency Rating',
            'value': product.efficiency_rating,
            'icon': 'fas fa-star'
        })
    
    context = {
        'product': product,
        'related_products': related_products,
        'specifications': specifications,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
        'in_cart': in_cart,
        'cart_quantity': cart_quantity,
        'page_title': f'{product.name} - BlueWave Solutions',
    }
    return render(request, 'products/product_detail.html', context)

def category_detail(request, category_id):
    """
    Category detail view showing all products in a category
    """
    category = get_object_or_404(ProductCategory, id=category_id, is_active=True)
    
    products = Product.objects.filter(
        product_category=category,
        is_active=True
    ).order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': products,
        'page_title': f'{category.name} - BlueWave Solutions',
    }
    return render(request, 'products/category_detail.html', context)

@login_required
def product_compare(request):
    """
    Product comparison view
    """
    product_ids = request.GET.getlist('products')
    
    if not product_ids:
        messages.warning(request, 'Please select products to compare.')
        return redirect('products:product_list')
    
    if len(product_ids) > 4:
        messages.warning(request, 'You can compare up to 4 products at once.')
        product_ids = product_ids[:4]
    
    products = Product.objects.filter(
        id__in=product_ids,
        is_active=True
    ).select_related('product_category')
    
    if not products:
        messages.error(request, 'No valid products found for comparison.')
        return redirect('products:product_list')
    
    # Create comparison matrix
    comparison_fields = [
        {'name': 'Price', 'field': 'price', 'format': 'currency'},
        {'name': 'Daily Capacity', 'field': 'capacity_gallons_per_day', 'format': 'gallons'},
        {'name': 'Power Consumption', 'field': 'power_consumption_watts', 'format': 'watts'},
        {'name': 'Energy Source', 'field': 'energy_source', 'format': 'text'},
        {'name': 'Daily CO₂ Savings', 'field': 'daily_co2_savings', 'format': 'kg'},
        {'name': 'Environmental Score', 'field': 'environmental_score', 'format': 'score'},
        {'name': 'Efficiency', 'field': 'efficiency_rating', 'format': 'text'},
        {'name': 'Stock', 'field': 'stock_quantity', 'format': 'number'},
    ]
    
    context = {
        'products': products,
        'comparison_fields': comparison_fields,
        'page_title': 'Product Comparison - BlueWave Solutions',
    }
    return render(request, 'products/product_compare.html', context)

def search_products(request):
    """
    AJAX search endpoint for autocomplete
    """
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    ).select_related('product_category')[:10]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'category': product.product_category.name if product.product_category else '',
            'price': str(product.price),
            'image': product.image.url if product.image else '',
            'url': product.get_absolute_url()
        })
    
    return JsonResponse({'results': results})

@login_required
def add_review(request, pk):
    """
    Add a product review
    """
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # Check if user already reviewed this product
    existing_review = ProductReview.objects.filter(product=product, user=request.user).first()
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        review_text = request.POST.get('review_text')
        
        if not all([rating, title, review_text]):
            messages.error(request, 'All fields are required.')
            return redirect('products:product_detail', pk=pk)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid rating.')
            return redirect('products:product_detail', pk=pk)
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.title = title
            existing_review.review_text = review_text
            existing_review.save()
            messages.success(request, 'Your review has been updated!')
        else:
            # Create new review
            ProductReview.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                title=title,
                review_text=review_text
            )
            messages.success(request, 'Thank you for your review!')
        
        return redirect('products:product_detail', pk=pk)
    
    context = {
        'product': product,
        'existing_review': existing_review,
        'page_title': f'Review {product.name} - BlueWave Solutions',
    }
    return render(request, 'products/add_review.html', context)