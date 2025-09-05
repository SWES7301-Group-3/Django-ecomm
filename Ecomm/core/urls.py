from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('api-docs/', views.api_docs_view, name='api_docs'),
    
    # AJAX endpoints
    path('newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
    path('health/', views.health_check_view, name='health_check'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
]