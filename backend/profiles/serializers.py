from rest_framework import serializers
from .models import VendorProfile, CustomerProfile

class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = ['id', 'store_name', 'description', 'logo', 'address', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['id', 'address', 'phone', 'preferences', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']