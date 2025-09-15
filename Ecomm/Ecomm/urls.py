from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # 2FA
    #path("account/", include("two_factor.urls")),  # 2FA routes
    #path("2fa/", include("two_factor.urls")),  # Include the 2FA URLs


    # Core app (main pages)
    path("", include("core.urls")),
    
    # Feature apps
    path("accounts/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("subscriptions/", include("subscriptions.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)