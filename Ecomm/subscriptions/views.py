from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from .models import SubscriptionPlan, UserSubscription, PaymentHistory
from .jwt_service import JWTSubscriptionService
import json
import stripe

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscription_plans(request):
    """Display available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    current_subscription = UserSubscription.objects.filter(
        user=request.user, is_active=True, end_date__gt=timezone.now()
    ).first()
    
    # Add user's subscription info to context
    user_subscriptions = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).select_related('plan')
    
    return render(request, 'subscriptions/plans.html', {
        'plans': plans,
        'current_subscription': current_subscription,
        'user_subscriptions': user_subscriptions,
        'page_title': 'Subscription Plans - BlueWave Solutions'
    })

@login_required
def subscribe(request, plan_id):
    """Subscribe to a specific plan with Stripe or PayPal payment"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
    # Check if user already has this specific plan active
    existing_subscription = UserSubscription.objects.filter(
        user=request.user, 
        plan=plan,
        is_active=True, 
        end_date__gt=timezone.now()
    ).first()
    
    if existing_subscription:
        messages.warning(request, f'You already have an active {plan.name} subscription.')
        return redirect('subscriptions:my_subscriptions')
    
    if request.method == 'POST':
        # Check payment method
        stripe_token = request.POST.get('stripeToken')
        paypal_order_id = request.POST.get('paypalOrderId')
        paypal_payer_email = request.POST.get('paypalPayerEmail')
        
        if not stripe_token and not paypal_order_id:
            messages.error(request, 'Payment information is required.')
            return render(request, 'subscriptions/subscribe.html', {
                'plan': plan,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Subscribe to {plan.name}'
            })
        
        # Determine payment method
        payment_method = 'paypal' if paypal_order_id else 'stripe'
        
        try:
            # Start a database transaction
            with transaction.atomic():
                # Create subscription first
                subscription = UserSubscription.objects.create(
                    user=request.user, 
                    plan=plan,
                    payment_method=payment_method
                )
                
                # Create PaymentHistory record with the subscription
                payment_record = PaymentHistory.objects.create(
                    subscription=subscription,  # Now we have a valid subscription
                    amount=plan.price,
                    currency='USD',
                    status='pending'
                )
                
                # Process payment based on method
                if stripe_token:
                    # Process Stripe payment
                    charge = stripe.Charge.create(
                        amount=int(plan.price * 100),  # Stripe expects amount in cents
                        currency='usd',
                        description=f'Subscription to {plan.name} by {request.user.username}',
                        source=stripe_token,
                        metadata={
                            'user_id': request.user.id,
                            'user_email': request.user.email,
                            'plan_id': plan.id,
                            'plan_name': plan.name,
                            'subscription_id': subscription.id,
                            'payment_record_id': payment_record.id
                        }
                    )
                    payment_id = charge.id
                    
                elif paypal_order_id:
                    # For PayPal, we assume the payment was already captured
                    # In production, you should verify the payment with PayPal API
                    payment_id = paypal_order_id
                
                # Update payment record with success
                payment_record.stripe_payment_intent_id = payment_id
                payment_record.status = 'completed'
                payment_record.save()
                
                messages.success(request, f'Successfully subscribed to {plan.name}!')
                return redirect('subscriptions:subscription_success', subscription_id=subscription.id)
                
        except stripe.error.CardError as e:
            # Payment failed - update payment record if it exists
            if 'payment_record' in locals():
                payment_record.status = 'failed'
                payment_record.failure_reason = f'Card error: {e.user_message}'
                payment_record.save()
            
            messages.error(request, f'Card error: {e.user_message}')
            return render(request, 'subscriptions/subscribe.html', {
                'plan': plan,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Subscribe to {plan.name}'
            })
            
        except stripe.error.StripeError as e:
            # Payment failed - update payment record if it exists
            if 'payment_record' in locals():
                payment_record.status = 'failed'
                payment_record.failure_reason = f'Payment failed: {str(e)}'
                payment_record.save()
            
            messages.error(request, f'Payment failed: {str(e)}')
            return render(request, 'subscriptions/subscribe.html', {
                'plan': plan,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Subscribe to {plan.name}'
            })
            
        except Exception as e:
            # Payment failed - update payment record if it exists
            if 'payment_record' in locals():
                payment_record.status = 'failed'
                payment_record.failure_reason = f'Subscription failed: {str(e)}'
                payment_record.save()
            
            messages.error(request, f'Subscription failed: {str(e)}')
            return render(request, 'subscriptions/subscribe.html', {
                'plan': plan,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Subscribe to {plan.name}'
            })
    
    return render(request, 'subscriptions/subscribe.html', {
        'plan': plan,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'page_title': f'Subscribe to {plan.name}'
    })

@login_required 
def renew_subscription(request, subscription_id):
    """Renew an expired subscription with Stripe payment"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    
    if subscription.is_valid:
        messages.warning(request, 'This subscription is still active.')
        return redirect('subscriptions:my_subscriptions')
    
    if request.method == 'POST':
        # Get Stripe token from form
        stripe_token = request.POST.get('stripeToken')
        
        if not stripe_token:
            messages.error(request, 'Payment information is required.')
            return render(request, 'subscriptions/renew.html', {
                'subscription': subscription,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Renew {subscription.plan.name}'
            })
        
        # Create PaymentHistory record first
        payment_record = PaymentHistory.objects.create(
            subscription=None,  # Will be updated after subscription creation
            amount=subscription.plan.price,
            currency='USD',
            status='pending'
        )
        
        try:
            # Create Stripe charge for renewal
            charge = stripe.Charge.create(
                amount=int(subscription.plan.price * 100),  # Stripe expects amount in cents
                currency='usd',
                description=f'Renewal of {subscription.plan.name} by {request.user.username}',
                source=stripe_token,
                metadata={
                    'user_id': request.user.id,
                    'user_email': request.user.email,
                    'plan_id': subscription.plan.id,
                    'plan_name': subscription.plan.name,
                    'renewal': True,
                    'original_subscription_id': subscription.id,
                    'payment_record_id': payment_record.id
                }
            )
            
            # Create new subscription (renewal) only if payment succeeded
            new_subscription = subscription.renew()
            
            # Update payment record with subscription and charge details
            payment_record.subscription = new_subscription
            payment_record.stripe_payment_intent_id = charge.id  # Store charge ID
            payment_record.status = 'completed'
            payment_record.save()
            
            messages.success(request, f'Successfully renewed {subscription.plan.name}!')
            return redirect('subscriptions:subscription_success', subscription_id=new_subscription.id)
            
        except stripe.error.CardError as e:
            # Update payment record with failure details
            payment_record.status = 'failed'
            payment_record.failure_reason = f'Card error: {e.user_message}'
            payment_record.save()
            
            messages.error(request, f'Card error: {e.user_message}')
            return render(request, 'subscriptions/renew.html', {
                'subscription': subscription,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Renew {subscription.plan.name}'
            })
            
        except stripe.error.StripeError as e:
            # Update payment record with failure details
            payment_record.status = 'failed'
            payment_record.failure_reason = f'Payment failed: {str(e)}'
            payment_record.save()
            
            messages.error(request, f'Payment failed: {str(e)}')
            return render(request, 'subscriptions/renew.html', {
                'subscription': subscription,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Renew {subscription.plan.name}'
            })
            
        except Exception as e:
            # Update payment record with failure details
            payment_record.status = 'failed'
            payment_record.failure_reason = f'Renewal failed: {str(e)}'
            payment_record.save()
            
            messages.error(request, f'Renewal failed: {str(e)}')
            return render(request, 'subscriptions/renew.html', {
                'subscription': subscription,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'page_title': f'Renew {subscription.plan.name}'
            })
    
    return render(request, 'subscriptions/renew.html', {
        'subscription': subscription,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'page_title': f'Renew {subscription.plan.name}'
    })

@login_required
def subscription_success(request, subscription_id):
    """Subscription success page with API token"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    
    # Generate API token
    api_token = None
    try:
        api_token = JWTSubscriptionService.generate_subscription_token(request.user, subscription)
    except Exception as e:
        messages.warning(request, f'Token generation failed: {str(e)}')
    
    # Get payment information
    latest_payment = subscription.payments.filter(status='completed').first()
    
    return render(request, 'subscriptions/success.html', {
        'subscription': subscription,
        'payment': latest_payment,
        'api_token': api_token,
        'flask_api_url': 'http://localhost:5000/api/v1',
        'page_title': 'Subscription Successful'
    })

@login_required
def cancel_subscription(request, subscription_id):
    """Cancel a specific subscription"""
    subscription = get_object_or_404(
        UserSubscription, 
        id=subscription_id, 
        user=request.user
    )
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        subscription.cancel(reason=reason)  # Using the model method
        messages.success(request, f'Your {subscription.plan.name} subscription has been cancelled.')
        return redirect('subscriptions:my_subscriptions')
    
    return render(request, 'subscriptions/cancel.html', {
        'subscription': subscription,
        'page_title': f'Cancel {subscription.plan.name}'
    })

@login_required
def my_subscriptions(request):
    """Display user's subscription history with API tokens"""
    subscriptions = UserSubscription.objects.filter(
        user=request.user
    ).select_related('plan').prefetch_related('payments').order_by('-start_date')
    
    active_subscription = subscriptions.filter(
        is_active=True, 
        end_date__gt=timezone.now()
    ).first()
    
    # Generate API tokens for active subscriptions and structure data
    subscription_data = []
    
    for subscription in subscriptions:
        token = None
        if subscription.is_valid:
            try:
                token = JWTSubscriptionService.generate_subscription_token(request.user, subscription)
            except Exception as e:
                print(f"Token generation failed for subscription {subscription.id}: {str(e)}")
        
        # Calculate progress percentage
        if subscription.plan.duration_days > 0:
            days_used = subscription.plan.duration_days - subscription.days_remaining
            progress_percentage = (days_used / subscription.plan.duration_days) * 100
        else:
            progress_percentage = 0
        
        # Get payment information
        latest_payment = subscription.payments.filter(status='completed').first()
        
        # Add subscription with all calculated data
        subscription_data.append({
            'subscription': subscription,
            'api_token': token,
            'progress_percentage': min(100, max(0, progress_percentage)),
            'payment': latest_payment
        })
    
    return render(request, 'subscriptions/my_subscriptions.html', {
        'subscription_data': subscription_data,
        'subscriptions': subscriptions,
        'active_subscription': active_subscription,
        'page_title': 'My Subscriptions'
    })

@login_required
def api_dashboard(request):
    """API dashboard with JWT token generation"""
    if request.user.is_superuser or request.user.is_staff:
        token = JWTSubscriptionService.generate_admin_token(request.user)
        subscription = None
        is_admin = True
    else:
        subscription = UserSubscription.objects.filter(
            user=request.user, is_active=True, end_date__gt=timezone.now()
        ).first()
        
        if not subscription:
            messages.warning(request, 'You need an active subscription to access the API.')
            return redirect('subscriptions:subscription_plans')
        
        token = JWTSubscriptionService.generate_subscription_token(request.user, subscription)
        is_admin = False
    
    # Get API usage stats if available
    api_usage = {}
    if subscription:
        # You can implement usage tracking here
        api_usage = {
            'calls_today': 0,  # Implement usage tracking
            'limit': subscription.plan.api_rate_limit,
            'percentage': 0
        }
    
    return render(request, 'subscriptions/dashboard.html', {
        'token': token,
        'subscription': subscription,
        'is_admin': is_admin,
        'is_advanced_user': subscription and subscription.plan.plan_type != 'basic_user',
        'api_usage': api_usage,
        'flask_api_url': 'http://localhost:5000/api/v1',
        'page_title': 'API Dashboard'
    })

@login_required
def payment_history(request):
    """View payment history for user's subscriptions"""
    payments = PaymentHistory.objects.filter(
        subscription__user=request.user
    ).select_related('subscription', 'subscription__plan').order_by('-payment_date')
    
    return render(request, 'subscriptions/payment_history.html', {
        'payments': payments,
        'page_title': 'Payment History'
    })

@csrf_exempt
def verify_subscription_token(request):
    """API endpoint to verify JWT tokens - enhanced for Flask compatibility"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'valid': False, 'error': 'Token not provided'})
        
        # Verify token using your existing service
        payload = JWTSubscriptionService.verify_token(token)
        
        # Create Flask-compatible response
        response_data = JWTSubscriptionService.create_flask_response(payload)
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)}, status=500)
    
@login_required
def subscription_status(request):
    """Get current subscription status as JSON - enhanced"""
    subscription = UserSubscription.objects.filter(
        user=request.user, is_active=True, end_date__gt=timezone.now()
    ).first()
    
    if subscription:
        # Generate current token
        try:
            current_token = JWTSubscriptionService.generate_subscription_token(request.user, subscription)
        except Exception:
            current_token = None
            
        return JsonResponse({
            'has_subscription': True,
            'plan_name': subscription.plan.name,
            'plan_type': subscription.plan.plan_type,
            'end_date': subscription.end_date.isoformat(),
            'days_remaining': subscription.days_remaining,
            'rate_limit': subscription.plan.api_rate_limit,
            'features': subscription.plan.features,
            'auto_renew': subscription.auto_renew,
            'current_token': current_token,
            'subscription_id': subscription.id
        })
    else:
        return JsonResponse({
            'has_subscription': False,
            'is_admin': request.user.is_superuser or request.user.is_staff,
            'admin_token': JWTSubscriptionService.generate_admin_token(request.user) if request.user.is_staff else None
        })

@login_required
def download_api_docs(request):
    """Download API documentation"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    # Check if user has active subscription or is admin
    has_access = (
        request.user.is_staff or 
        UserSubscription.objects.filter(
            user=request.user, 
            is_active=True, 
            end_date__gt=timezone.now()
        ).exists()
    )
    
    if not has_access:
        messages.warning(request, 'You need an active subscription to access API documentation.')
        return redirect('subscriptions:subscription_plans')
    
    return render(request, 'subscriptions/api_docs.html', {
        'page_title': 'API Documentation'
    })