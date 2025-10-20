from rest_framework import serializers
from .models import ShippingAddress, ShippingRate, OrderCancellation, ReturnRequest
from products.models import Product


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['id', 'user', 'label', 'recipient_name', 'phone', 'street_address', 
                 'apartment', 'city', 'state', 'postal_code', 'country', 'is_default', 
                 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class ShippingRateSerializer(serializers.ModelSerializer):
    estimated_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = ShippingRate
        fields = ['id', 'carrier', 'service_name', 'base_cost', 'cost_per_kg', 'cost_per_km',
                 'min_delivery_days', 'max_delivery_days', 'is_active', 'estimated_cost']
    
    def get_estimated_cost(self, obj):
        # Get weight and distance from context if provided
        weight = self.context.get('weight', 1)
        distance = self.context.get('distance', 0)
        return str(obj.calculate_cost(weight, distance))


class OrderCancellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderCancellation
        fields = ['id', 'order', 'reason', 'details', 'requested_by', 'approved_by',
                 'refund_amount', 'refund_processed', 'refund_transaction_id', 
                 'created_at', 'processed_at']
        read_only_fields = ['requested_by', 'approved_by', 'refund_processed', 
                           'refund_transaction_id', 'created_at', 'processed_at']


class ReturnRequestSerializer(serializers.ModelSerializer):
    items_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ReturnRequest
        fields = ['id', 'rma_number', 'order', 'vendor_order', 'items', 'items_details',
                 'reason', 'description', 'images', 'status', 'refund_amount', 
                 'restocking_fee', 'refund_method', 'refund_transaction_id', 'vendor_notes',
                 'created_at', 'approved_at', 'received_at', 'refunded_at']
        read_only_fields = ['rma_number', 'status', 'refund_transaction_id', 
                           'created_at', 'approved_at', 'received_at', 'refunded_at']
    
    def get_items_details(self, obj):
        items_data = []
        for item in obj.items.all():
            items_data.append({
                'id': str(item.id),
                'product_name': item.product.name if item.product else 'N/A',
                'quantity': item.quantity,
                'unit_price': str(item.unit_price)
            })
        return items_data

