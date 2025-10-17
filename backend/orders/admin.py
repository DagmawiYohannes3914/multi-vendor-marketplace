from django.contrib import admin
from .models import Cart, CartItem, Reservation, Order, OrderItem, VendorOrder

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "sku", "quantity", "unit_price")

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("sku", "user", "quantity", "expires_at", "status")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at")

@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ("order", "vendor", "status", "total_amount")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "sku", "quantity", "unit_price")