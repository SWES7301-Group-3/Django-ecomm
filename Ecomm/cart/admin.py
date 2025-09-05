from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    readonly_fields = ("line_total", "unit_price", "product")
    fields = ("product", "quantity", "unit_price", "line_total", "metadata")
    extra = 0
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "is_active", "item_count", "subtotal", "total", "updated_at")
    list_filter = ("is_active", "updated_at")
    search_fields = ("user__username", "session_key", "id")
    inlines = [CartItemInline]
    readonly_fields = ("subtotal", "total", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user", "session_key", "is_active", "metadata")}),
        ("Totals", {"fields": ("subtotal", "total")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def item_count(self, obj):
        return obj.item_count
    item_count.short_description = "Items"