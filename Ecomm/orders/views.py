from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order

@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'page_title': 'Order History'
    }
    return render(request, 'orders/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'page_title': f'Order #{order.id}'
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def create_order(request):
    """Create order from cart"""
    # This would typically handle order creation
    # For now, just redirect to cart
    messages.info(request, 'Order creation is not yet implemented.')
    return redirect('cart:cart_detail')

@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status not in ['pending', 'processing']:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been cancelled.')
        return redirect('orders:order_history')
    
    context = {
        'order': order,
        'page_title': 'Cancel Order'
    }
    return render(request, 'orders/cancel_order.html', context)