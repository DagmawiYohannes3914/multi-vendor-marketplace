# test_serializers.py - Script to test serializers with first_name and last_name

# This script should be run with: python manage.py shell < test_serializers.py

from accounts.serializers import UserSerializer
from profiles.serializers import VendorProfileSerializer, CustomerProfileSerializer

# Test UserSerializer with first_name and last_name
print("\nTesting UserSerializer:")
user_data = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'password123',
    'first_name': 'Test',
    'last_name': 'User',
    'is_vendor': True,
    'is_customer': False
}

user_serializer = UserSerializer(data=user_data)
if user_serializer.is_valid():
    print("UserSerializer validation successful")
    print(f"Validated data: {user_serializer.validated_data}")
    print(f"First name: {user_serializer.validated_data.get('first_name')}")
    print(f"Last name: {user_serializer.validated_data.get('last_name')}")
else:
    print(f"UserSerializer validation errors: {user_serializer.errors}")

# Test VendorProfileSerializer fields
print("\nVendorProfileSerializer fields:")
vendor_serializer = VendorProfileSerializer()
print(f"Fields: {vendor_serializer.fields.keys()}")
print(f"Has first_name: {'first_name' in vendor_serializer.fields}")
print(f"Has last_name: {'last_name' in vendor_serializer.fields}")

# Test CustomerProfileSerializer fields
print("\nCustomerProfileSerializer fields:")
customer_serializer = CustomerProfileSerializer()
print(f"Fields: {customer_serializer.fields.keys()}")
print(f"Has first_name: {'first_name' in customer_serializer.fields}")
print(f"Has last_name: {'last_name' in customer_serializer.fields}")

print("\nTest completed!")