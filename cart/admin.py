from django.contrib import admin

from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "updated_at")
    search_fields = ("user__username",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "game", "quantity", "price_snapshot")
    search_fields = ("cart__user__username", "game__title")
