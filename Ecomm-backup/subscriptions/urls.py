from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_list, name='subscription_list'),
    path('plans/', views.plan_list, name='plan_list'),
    path('subscribe/<int:plan_id>/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
]