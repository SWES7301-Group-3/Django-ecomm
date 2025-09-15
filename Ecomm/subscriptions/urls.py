from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Main subscription pages
    path('', views.subscription_plans, name='subscription_plans'),  # /subscriptions/
    path('plans/', views.subscription_plans, name='plan_list'),     # Alternative URL for compatibility
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('success/<int:subscription_id>/', views.subscription_success, name='subscription_success'),
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    path('payment-history/', views.payment_history, name='payment_history'),
    
    # API related
    path('dashboard/', views.api_dashboard, name='api_dashboard'),
    path('verify-token/', views.verify_subscription_token, name='verify_token'),
    path('status/', views.subscription_status, name='subscription_status'),
    path('api-docs/', views.download_api_docs, name='api_docs'),

]