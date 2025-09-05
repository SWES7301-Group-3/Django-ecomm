from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("line_total",)
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "total_amount")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline]
    search_fields = ("user__username", "id")