from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SubscriptionPlan, UserSubscription

def subscription_list(request):
    """Display subscription plans"""
    return redirect('subscriptions:plan_list')

def plan_list(request):
    """Display available subscription plans"""
    plans = SubscriptionPlan.objects.filter(active=True).order_by('price_per_month')
    
    context = {
        'plans': plans,
        'page_title': 'Data Subscription Plans'
    }
    return render(request, 'subscriptions/plan_list.html', context)

@login_required
def my_subscriptions(request):
    """Display user's subscriptions"""
    subscriptions = UserSubscription.objects.filter(user=request.user).select_related('plan').order_by('-start_date')
    
    context = {
        'subscriptions': subscriptions,
        'page_title': 'My Subscriptions'
    }
    return render(request, 'subscriptions/my_subscriptions.html', context)

@login_required
def subscribe_to_plan(request, plan_id):
    """Subscribe to a plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, active=True)
    
    # Check if user already has this subscription
    existing = UserSubscription.objects.filter(user=request.user, plan=plan, status='active').first()
    if existing:
        messages.warning(request, f'You already have an active subscription to {plan.name}.')
        return redirect('subscriptions:my_subscriptions')
    
    # Create subscription (simplified - in real app you'd handle payment here)
    subscription = UserSubscription.objects.create(
        user=request.user,
        plan=plan,
        status='active'
    )
    
    messages.success(request, f'Successfully subscribed to {plan.name}!')
    return redirect('subscriptions:my_subscriptions')

@login_required
def cancel_subscription(request, subscription_id):
    """Cancel a subscription"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.cancel_at_period_end = True
        subscription.save()
        
        messages.success(request, f'Cancelled subscription to {subscription.plan.name}.')
        return redirect('subscriptions:my_subscriptions')
    
    context = {
        'subscription': subscription,
        'page_title': 'Cancel Subscription'
    }
    return render(request, 'subscriptions/cancel_subscription.html', context)