from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VendorProfile, CustomerProfile, VendorReview

User = get_user_model()

class VendorReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorReview
        fields = ['id', 'vendor', 'customer', 'customer_name', 'order', 'rating', 
                 'review_text', 'created_at', 'is_approved']
        read_only_fields = ['customer', 'is_approved']
    
    def get_customer_name(self, obj):
        return obj.customer.username
    
    def create(self, validated_data):
        # Set the customer to the current user
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)


class VendorProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    reviews = VendorReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = ['id', 'user_id', 'username', 'first_name', 'last_name', 'store_name', 
                 'description', 'logo', 'address', 'phone', 'average_rating', 
                 'total_reviews', 'reviews', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'username', 'first_name', 'last_name', 
                           'average_rating', 'total_reviews', 'reviews', 'created_at', 'updated_at']

class CustomerProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = ['id', 'user_id', 'username', 'first_name', 'last_name', 'address', 'phone', 'preferences', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'username', 'first_name', 'last_name', 'created_at', 'updated_at']