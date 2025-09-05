from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path("register/", views.RegisterAPIView.as_view(), name="api-register"),
    path("token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", views.LogoutAPIView.as_view(), name="api-logout"),
    
    # User endpoints
    path("me/", views.MeAPIView.as_view(), name="api-me"),
    path("users/", views.UserListAPIView.as_view(), name="api-users-list"),  # Admin only
]