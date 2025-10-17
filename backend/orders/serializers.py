from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Cart, CartItem, Reservation, Order, OrderItem, VendorOrder
from products.serializers import SKUSerializer, ProductSerializer

User = get_user_model()


class CartItemSerializer(serializers.ModelSerializer):
    sku_detail = SKUSerializer(source="sku", read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "sku", "sku_detail", "quantity", "unit_price", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "created_at", "updated_at"]
        read_only_fields = ["user"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "sku", "product", "quantity", "unit_price"]


class VendorOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = VendorOrder
        fields = ["id", "vendor", "status", "total_amount", "items"]


class OrderSerializer(serializers.ModelSerializer):
    vendor_orders = VendorOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "payment_method", "total_amount", "currency", "payment_intent_id", "created_at", "vendor_orders"]
        read_only_fields = ["user", "payment_intent_id"]