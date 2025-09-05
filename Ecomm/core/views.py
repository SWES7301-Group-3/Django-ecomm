from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import logging

from products.models import Product, ProductCategory
from orders.models import Order
from subscriptions.models import UserSubscription, SubscriptionPlan  # Changed from Subscription to UserSubscription
from cart.models import Cart
from .models import SiteSettings, ContactMessage, Newsletter, SystemStats
from .forms import ContactForm, NewsletterForm

User = get_user_model()
logger = logging.getLogger(__name__)

def landing_page(request):
    """
    BlueWave Solutions Landing Page
    Showcases desalination units and data subscription services
    """
    # Get site settings
    site_settings = SiteSettings.get_settings()
    
    # Get featured products
    featured_products = Product.objects.filter(
        is_featured=True, 
        is_active=True
    ).select_related('product_category')[:6]
    
    # Get product categories
    categories = ProductCategory.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    # Get today's stats
    today_stats = SystemStats.get_today_stats()
    
    # Environmental impact statistics
    environmental_stats = {
        'total_units_sold': today_stats.total_products_sold,
        'active_subscriptions': today_stats.active_subscriptions,
        'research_institutions': UserSubscription.objects.filter(  # Changed from Subscription
            status='active',  # Changed from active=True to status='active'
            plan__name__icontains='research'
        ).count(),
        'gallons_produced_daily': site_settings.total_gallons_processed,
        'co2_saved_total': float(site_settings.total_co2_saved),
        'countries_served': 45,  # Static for now
    }
    
    # Newsletter form
    newsletter_form = NewsletterForm()
    
    context = {
        'site_settings': site_settings,
        'featured_products': featured_products,
        'categories': categories,
        'environmental_stats': environmental_stats,
        'newsletter_form': newsletter_form,
        'page_title': f'{site_settings.site_name} - {site_settings.site_tagline}',
        'current_time': timezone.now(),
    }
    return render(request, 'core/landing.html', context)

@login_required
def dashboard_view(request):
    """
    User Dashboard - shows orders, subscriptions, and account overview
    """
    user = request.user
    
    # Get user's recent orders
    recent_orders = Order.objects.filter(user=user).select_related().order_by('-created_at')[:5]
    
    # Get user's active subscriptions (using UserSubscription and status='active')
    active_subscriptions = UserSubscription.objects.filter(  # Changed from Subscription
        user=user, 
        status='active'  # Changed from active=True to status='active'
    ).select_related('plan').order_by('-start_date')
    
    # Get cart items count
    cart_count = 0
    try:
        if hasattr(user, 'cart'):
            cart_count = user.cart.items.count()
    except:
        cart_count = 0
    
    # Calculate user statistics
    user_stats = {
        'total_orders': Order.objects.filter(user=user).count(),
        'completed_orders': Order.objects.filter(user=user, status='completed').count(),
        'total_spent': Order.objects.filter(
            user=user, status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'active_subscriptions_count': active_subscriptions.count(),
        'account_age_days': (timezone.now().date() - user.date_joined.date()).days,
    }
    
    # Environmental impact for user
    user_environmental_impact = {
        'gallons_processed': user_stats['completed_orders'] * 1250,  # Estimated
        'co2_saved': user_stats['completed_orders'] * 45,  # Estimated kg CO2
        'trees_equivalent': user_stats['completed_orders'] * 2,  # Tree equivalency
        'energy_generated': user_stats['completed_orders'] * 320,  # kWh solar
    }
    
    # Recent activity
    recent_activity = []
    
    # Add recent orders to activity
    for order in recent_orders[:3]:
        recent_activity.append({
            'icon': 'fas fa-shopping-bag',
            'action': f'Order #{order.id} {order.status}',
            'timestamp': order.created_at,
            'color': 'success' if order.status == 'completed' else 'info'
        })
    
    # Add subscription activity
    for subscription in active_subscriptions[:2]:
        recent_activity.append({
            'icon': 'fas fa-database',
            'action': f'Subscribed to {subscription.plan.name}',
            'timestamp': subscription.start_date,
            'color': 'warning'
        })
    
    # Add login activity
    if user.last_login:
        recent_activity.append({
            'icon': 'fas fa-sign-in-alt',
            'action': 'Logged in',
            'timestamp': user.last_login,
            'color': 'primary'
        })
    
    # Sort activity by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'recent_orders': recent_orders,
        'active_subscriptions': active_subscriptions,
        'cart_count': cart_count,
        'user_stats': user_stats,
        'user_environmental_impact': user_environmental_impact,
        'recent_activity': recent_activity[:5],
        'page_title': f'Dashboard - {user.get_full_name() or user.username}',
        'current_time': timezone.now(),
    }
    return render(request, 'core/dashboard.html', context)

def about_view(request):
    """About BlueWave Solutions"""
    site_settings = SiteSettings.get_settings()
    today_stats = SystemStats.get_today_stats()
    
    # Company timeline
    timeline = [
        {
            'year': '2020',
            'title': 'Foundation',
            'description': 'BlueWave Solutions was founded with a mission to provide sustainable water solutions.',
            'icon': 'fas fa-rocket'
        },
        {
            'year': '2021',
            'title': 'First Product Launch',
            'description': 'Launched our first solar-powered micro-desalination unit.',
            'icon': 'fas fa-tint'
        },
        {
            'year': '2022',
            'title': 'IoT Integration',
            'description': 'Integrated IoT sensors for real-time environmental monitoring.',
            'icon': 'fas fa-wifi'
        },
        {
            'year': '2023',
            'title': 'Research Partnerships',
            'description': 'Established partnerships with leading research institutions worldwide.',
            'icon': 'fas fa-university'
        },
        {
            'year': '2024',
            'title': 'Global Expansion',
            'description': 'Expanded operations to serve customers in over 45 countries.',
            'icon': 'fas fa-globe'
        },
    ]
    
    # Team members
    team_members = [
        {
            'name': 'Dr. Sarah Martinez',
            'position': 'CEO & Founder',
            'bio': 'Environmental engineer with 15 years of experience in water purification technologies.',
            'image': 'core/team/sarah.jpg'
        },
        {
            'name': 'Michael Chen',
            'position': 'CTO',
            'bio': 'IoT and renewable energy systems expert, former Tesla engineer.',
            'image': 'core/team/michael.jpg'
        },
        {
            'name': 'Dr. Amara Okafor',
            'position': 'Head of Research',
            'bio': 'Marine biologist specializing in ocean water quality and desalination processes.',
            'image': 'core/team/amara.jpg'
        },
        {
            'name': 'James Rodriguez',
            'position': 'VP of Engineering',
            'bio': 'Mechanical engineer with expertise in sustainable manufacturing and solar technology.',
            'image': 'core/team/james.jpg'
        },
    ]
    
    context = {
        'site_settings': site_settings,
        'today_stats': today_stats,
        'timeline': timeline,
        'team_members': team_members,
        'page_title': f'About {site_settings.site_name}',
    }
    return render(request, 'core/about.html', context)

def contact_view(request):
    """Contact page with form"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.user = request.user
            contact_message.save()
            
            logger.info(f"New contact message from {contact_message.email}: {contact_message.subject}")
            messages.success(request, 'Thank you for your message! We will get back to you within 24 hours.')
            return redirect('core:contact')
    else:
        # Pre-fill form if user is authenticated
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
        form = ContactForm(initial=initial_data)
    
    site_settings = SiteSettings.get_settings()
    
    context = {
        'form': form,
        'site_settings': site_settings,
        'page_title': 'Contact Us',
    }
    return render(request, 'core/contact.html', context)

def api_docs_view(request):
    """API Documentation page"""
    site_settings = SiteSettings.get_settings()
    
    # API endpoints documentation
    api_endpoints = [
        {
            'endpoint': '/api/v1/buoys/',
            'method': 'GET',
            'description': 'Get list of IoT buoys and their current status',
            'auth_required': True,
            'tier': 'Basic',
        },
        {
            'endpoint': '/api/v1/buoys/{id}/data/',
            'method': 'GET',
            'description': 'Get real-time data from specific buoy',
            'auth_required': True,
            'tier': 'Standard',
        },
        {
            'endpoint': '/api/v1/environmental-data/',
            'method': 'GET',
            'description': 'Get aggregated environmental data',
            'auth_required': True,
            'tier': 'Professional',
        },
        {
            'endpoint': '/api/v1/historical-data/',
            'method': 'GET',
            'description': 'Access historical environmental datasets',
            'auth_required': True,
            'tier': 'Research',
        },
        {
            'endpoint': '/api/v1/alerts/',
            'method': 'GET',
            'description': 'Get environmental alerts and notifications',
            'auth_required': True,
            'tier': 'Professional',
        },
    ]
    
    context = {
        'site_settings': site_settings,
        'api_endpoints': api_endpoints,
        'page_title': 'API Documentation',
    }
    return render(request, 'core/api_docs.html', context)

def newsletter_signup(request):
    """Newsletter signup via AJAX"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            try:
                newsletter = form.save()
                logger.info(f"New newsletter signup: {newsletter.email}")
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for subscribing to our newsletter!'
                })
            except:
                return JsonResponse({
                    'success': False,
                    'message': 'This email is already subscribed to our newsletter.'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

def health_check_view(request):
    """System health check endpoint"""
    try:
        # Check database connectivity
        user_count = User.objects.count()
        product_count = Product.objects.count()
        
        # Get system stats
        today_stats = SystemStats.get_today_stats()
        
        health_data = {
            "status": "healthy",
            "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "version": "1.0.0",
            "database": "connected",
            "services": {
                "authentication": "operational",
                "products": "operational",
                "orders": "operational",
                "subscriptions": "operational",
                "api": "operational"
            },
            "metrics": {
                "total_users": user_count,
                "total_products": product_count,
                "orders_today": today_stats.orders_today,
                "revenue_today": float(today_stats.revenue_today),
                "active_subscriptions": today_stats.active_subscriptions,
            },
            "current_user": request.user.username if request.user.is_authenticated else "anonymous",
            "session_active": request.user.is_authenticated,
        }
        
        return JsonResponse(health_data, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }, status=500)

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard_view(request):
    """Admin dashboard with system overview"""
    # Get system statistics
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    
    today_stats = SystemStats.get_today_stats()
    
    # Calculate growth percentages
    try:
        yesterday_stats = SystemStats.objects.get(date=yesterday)
        user_growth = ((today_stats.total_users - yesterday_stats.total_users) / yesterday_stats.total_users * 100) if yesterday_stats.total_users > 0 else 0
        revenue_growth = ((today_stats.total_revenue - yesterday_stats.total_revenue) / yesterday_stats.total_revenue * 100) if yesterday_stats.total_revenue > 0 else 0
    except SystemStats.DoesNotExist:
        user_growth = 0
        revenue_growth = 0
    
    # Recent activity
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    recent_messages = ContactMessage.objects.filter(is_read=False).order_by('-created_at')[:5]
    recent_subscriptions = UserSubscription.objects.select_related('user', 'plan').order_by('-start_date')[:10]  # Changed from Subscription
    
    context = {
        'today_stats': today_stats,
        'user_growth': user_growth,
        'revenue_growth': revenue_growth,
        'recent_orders': recent_orders,
        'recent_messages': recent_messages,
        'recent_subscriptions': recent_subscriptions,
        'page_title': 'Admin Dashboard',
        'current_time': timezone.now(),
    }
    return render(request, 'core/admin_dashboard.html', context)

# Error handlers
def custom_404_view(request, exception):
    """Custom 404 error page"""
    context = {
        'page_title': 'Page Not Found - BlueWave Solutions',
        'error_code': '404',
        'error_title': 'Page Not Found',
        'error_message': 'The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.',
        'current_time': timezone.now(),
    }
    return render(request, 'core/error.html', context, status=404)

def custom_500_view(request):
    """Custom 500 error page"""
    context = {
        'page_title': 'Server Error - BlueWave Solutions',
        'error_code': '500',
        'error_title': 'Internal Server Error',
        'error_message': 'We are experiencing technical difficulties. Please try again later or contact support.',
        'current_time': timezone.now(),
    }
    return render(request, 'core/error.html', context, status=500)