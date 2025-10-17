from rest_framework import serializers
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from orders.models import VendorOrder, OrderItem
from products.models import Product, SKU
from .models import VendorProfile


class VendorDashboardStatsSerializer(serializers.Serializer):
    """
    Serializer for vendor dashboard statistics
    """
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_reviews = serializers.IntegerField()
    
    # Period comparisons
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_last_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders_this_month = serializers.IntegerField()
    orders_last_month = serializers.IntegerField()


class VendorOrderItemSerializer(serializers.Serializer):
    """Simplified order item for vendor dashboard"""
    product_name = serializers.CharField()
    sku_code = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class VendorOrderListSerializer(serializers.Serializer):
    """
    Serializer for vendor order list view
    """
    id = serializers.UUIDField()
    order_id = serializers.UUIDField(source='order.id')
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField(source='order.payment_method')
    created_at = serializers.DateTimeField(source='order.created_at')
    estimated_delivery = serializers.DateField()
    tracking_number = serializers.CharField()
    items_count = serializers.IntegerField()
    
    def get_customer_name(self, obj):
        if obj.order.is_guest:
            return obj.order.guest_name or 'Guest Customer'
        elif obj.order.user:
            return f"{obj.order.user.first_name} {obj.order.user.last_name}".strip() or obj.order.user.username
        return 'Unknown'
    
    def get_customer_email(self, obj):
        if obj.order.is_guest:
            return obj.order.guest_email
        elif obj.order.user:
            return obj.order.user.email
        return 'N/A'


class VendorOrderDetailSerializer(serializers.Serializer):
    """
    Detailed serializer for a single vendor order
    """
    id = serializers.UUIDField()
    order_id = serializers.UUIDField(source='order.id')
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField(source='order.payment_method')
    payment_status = serializers.CharField(source='order.status')
    shipping_address = serializers.JSONField(source='order.shipping_address')
    tracking_number = serializers.CharField()
    carrier = serializers.CharField()
    estimated_delivery = serializers.DateField()
    shipped_at = serializers.DateTimeField()
    delivered_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField(source='order.created_at')
    items = VendorOrderItemSerializer(many=True)
    
    def get_customer_name(self, obj):
        if obj.order.is_guest:
            return obj.order.guest_name or 'Guest Customer'
        elif obj.order.user:
            return f"{obj.order.user.first_name} {obj.order.user.last_name}".strip() or obj.order.user.username
        return 'Unknown'
    
    def get_customer_email(self, obj):
        if obj.order.is_guest:
            return obj.order.guest_email
        elif obj.order.user:
            return obj.order.user.email
        return 'N/A'
    
    def get_customer_phone(self, obj):
        if obj.order.is_guest:
            return obj.order.guest_phone or 'N/A'
        elif obj.order.user and hasattr(obj.order.user, 'customer_profile'):
            return obj.order.user.customer_profile.phone or 'N/A'
        return 'N/A'


class VendorOrderUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating vendor order status
    """
    status = serializers.ChoiceField(choices=VendorOrder.STATUS_CHOICES)
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    carrier = serializers.CharField(required=False, allow_blank=True)
    estimated_delivery = serializers.DateField(required=False, allow_null=True)


class ProductPerformanceSerializer(serializers.Serializer):
    """
    Serializer for product performance metrics
    """
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_stock = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)
    total_reviews = serializers.IntegerField()


class LowStockAlertSerializer(serializers.Serializer):
    """
    Serializer for low stock alerts
    """
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    sku_code = serializers.CharField()
    sku_id = serializers.UUIDField()
    current_stock = serializers.IntegerField()
    status = serializers.CharField()


class RevenueReportSerializer(serializers.Serializer):
    """
    Serializer for revenue reports by period
    """
    period = serializers.CharField()  # e.g., "2024-01", "2024-W05", "2024-01-15"
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders_count = serializers.IntegerField()
    items_sold = serializers.IntegerField()

