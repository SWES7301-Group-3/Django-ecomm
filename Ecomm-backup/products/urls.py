from django.urls import path
from . import views
from . import admin_views

app_name = 'products'

urlpatterns = [
    # Public product views
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
    path('compare/', views.product_compare, name='product_compare'),
    path('search/', views.search_products, name='search_products'),
    
    # Admin product management
    path('admin/upload/', admin_views.admin_product_upload, name='admin_product_upload'),
    path('admin/list/', admin_views.admin_product_list, name='admin_product_list'),
    path('admin/bulk-upload/', admin_views.admin_bulk_upload, name='admin_bulk_upload'),
    path('admin/edit/<int:product_id>/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('admin/delete/<int:product_id>/', admin_views.admin_delete_product, name='admin_delete_product'),
    path('admin/categories/', admin_views.admin_category_management, name='admin_category_management'),
    path('admin/csv-template/', admin_views.download_csv_template, name='download_csv_template'),
    path('admin/delete-image/<int:image_id>/', admin_views.delete_product_image, name='delete_product_image'),
]