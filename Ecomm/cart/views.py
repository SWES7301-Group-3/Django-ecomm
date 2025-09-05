from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from products.models import Product
from .models import Cart, CartItem

@login_required
def cart_detail(request):
    """Display cart contents"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product').all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
    
    # Calculate totals
    subtotal = sum(item.get_total_price() for item in cart_items)
    shipping = 0 if subtotal > 500 else 25  # Free shipping over $500
    total = subtotal + shipping
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'page_title': 'Shopping Cart'
    }
    return render(request, 'cart/cart_detail.html', context)

@login_required
@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        messages.error(request, 'Invalid quantity.')
        return redirect('products:product_detail', pk=product_id)
    
    if quantity > product.stock_quantity:
        messages.error(request, f'Only {product.stock_quantity} items available in stock.')
        return redirect('products:product_detail', pk=product_id)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not item_created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            messages.error(request, f'Cannot add more items. Only {product.stock_quantity} available.')
            return redirect('products:product_detail', pk=product_id)
        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(request, f'Updated {product.name} quantity to {cart_item.quantity}.')
    else:
        messages.success(request, f'Added {product.name} to your cart.')
    
    return redirect('cart:cart_detail')

@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'Removed {product_name} from your cart.')
    return redirect('cart:cart_detail')

@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, f'Removed {cart_item.product.name} from your cart.')
    elif quantity > cart_item.product.stock_quantity:
        messages.error(request, f'Only {cart_item.product.stock_quantity} items available.')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f'Updated {cart_item.product.name} quantity.')
    
    return redirect('cart:cart_detail')

@login_required
@require_POST
def clear_cart(request):
    """Clear all items from cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        messages.success(request, 'Cart cleared successfully.')
    except Cart.DoesNotExist:
        messages.info(request, 'Your cart is already empty.')
    
    return redirect('cart:cart_detail')

@login_required
def checkout(request):
    """Checkout process"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product').all()
        
        if not cart_items:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart_detail')
        
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:product_list')
    
    # Calculate totals
    subtotal = sum(item.get_total_price() for item in cart_items)
    shipping = 0 if subtotal > 500 else 25
    total = subtotal + shipping
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'page_title': 'Checkout'
    }
    return render(request, 'cart/checkout.html', context)