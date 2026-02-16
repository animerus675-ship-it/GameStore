from django.contrib import admin

from .models import Order, OrderItem, Payment


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "game", "quantity", "price_snapshot")
    search_fields = ("order__id", "game__title")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "provider", "status", "paid_at")
    list_filter = ("status", "provider")
