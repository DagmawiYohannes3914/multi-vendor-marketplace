from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Cart, CartItem, Reservation, Order, OrderItem, VendorOrder, Coupon
from products.serializers import SKUSerializer, ProductSerializer

User = get_user_model()


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount_type', 'discount_value', 'min_purchase_amount', 
                 'is_active', 'valid_from', 'valid_to', 'max_uses', 'current_uses']
        read_only_fields = ['current_uses']


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
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    bulk_discount_applied = serializers.SerializerMethodField(read_only=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_name = serializers.CharField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    is_guest = serializers.BooleanField(required=False, default=False)
    
    def get_bulk_discount_applied(self, obj):
        # Check if any items have discounted prices
        regular_prices = {}
        for vendor_order in obj.vendor_orders.all():
            for item in vendor_order.items.all():
                product = item.product
                if product.id not in regular_prices:
                    regular_prices[product.id] = product.price
                
                # If unit price is less than product price, a discount was applied
                if item.unit_price < regular_prices[product.id]:
                    return True
        return False

    class Meta:
        model = Order
        fields = ["id", "user", "status", "payment_method", "total_amount", "subtotal_amount", 
                 "discount_amount", "coupon", "currency", "payment_intent_id", "tracking_number", 
                 "shipping_address", "estimated_delivery", "created_at", "updated_at", 
                 "vendor_orders", "coupon_code", "bulk_discount_applied", "guest_email", 
                 "guest_name", "guest_phone", "is_guest"]
        read_only_fields = ["user", "status", "total_amount", "subtotal_amount", "discount_amount", 
                           "coupon", "payment_intent_id", "bulk_discount_applied"]