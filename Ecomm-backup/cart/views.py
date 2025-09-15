from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from products.models import Product
from .models import Cart, CartItem
from orders.models import Order, OrderItem
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY


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
    subtotal = sum(item.line_total for item in cart_items)
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
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product').all()
        if not cart_items:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart_detail')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:product_list')

    subtotal = sum(item.line_total for item in cart_items)
    shipping = 0 if subtotal > 500 else 25
    total = subtotal + shipping

    if request.method == "POST":
        shipping_address = {
            "name": request.POST.get("shipping_name"),
            "address": request.POST.get("shipping_address"),
            "city": request.POST.get("shipping_city"),
            "state": request.POST.get("shipping_state"),
            "zip": request.POST.get("shipping_zip"),
            "country": request.POST.get("shipping_country"),
        }
        billing_address = {
            "name": request.POST.get("billing_name"),
            "address": request.POST.get("billing_address"),
            "city": request.POST.get("billing_city"),
            "state": request.POST.get("billing_state"),
            "zip": request.POST.get("billing_zip"),
            "country": request.POST.get("billing_country"),
        }
        # Validate required fields
        if not shipping_address["address"] or not shipping_address["zip"]:
            messages.error(request, "Shipping address is required.")
            return redirect("cart:checkout")

        # Stripe Payment
        token = request.POST.get("stripeToken")
        if not token:
            messages.error(request, "Payment information is required.")
            return redirect("cart:checkout")

        try:
            charge = stripe.Charge.create(
                amount=int(total * 100),  # Stripe expects amount in cents
                currency="usd",
                description=f"Order by {request.user.username}",
                source=token,
            )
        except stripe.error.CardError as e:
            messages.error(request, f"Card error: {e.user_message}")
            return redirect("cart:checkout")
        except stripe.error.StripeError as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect("cart:checkout")

        # Create Order only if payment succeeded
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            shipping_address=shipping_address,
            billing_address=billing_address,
            status="paid",  # Mark as paid
            metadata={"stripe_charge_id": charge.id}
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total
            )
            item.product.stock_quantity = max(item.product.stock_quantity - item.quantity, 0)
            item.product.save()
        cart.items.all().delete()
        cart.recalc_totals()
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect("orders:order_detail", order_id=order.id)

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "page_title": "Checkout",
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, "cart/checkout.html", context)