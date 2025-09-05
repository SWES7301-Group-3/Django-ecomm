from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_page, name="register_page"),
    path("login/", views.login_page, name="login_page"),
    path("logout/", views.logout_view, name="logout_view"),
    path("profile/", views.profile_page, name="profile_page"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile_view"),
    #path("about/", views.about_view, name="about_view"),
    #path("health/", views.health_check_view, name="health_check_view"),
    
    # Admin views (if user is staff)
    #path("admin/users/", views.admin_users_list_view, name="admin_users_list"),
    #path("admin/users/<int:user_id>/", views.admin_user_detail_view, name="admin_user_detail"),
]