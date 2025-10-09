# test_users.py - Script to test user creation with first and last names
import os
import django
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model
from profiles.models import VendorProfile, CustomerProfile

User = get_user_model()

# Clean up any existing test users
User.objects.filter(username__in=['testvendor', 'testcustomer']).delete()

# Create a vendor user directly with ORM
try:
    # Create vendor user
    vendor_user = User.objects.create_user(
        username='testvendor',
        email='vendor@example.com',
        password='password123',
        first_name='John',
        last_name='Seller',
        is_vendor=True,
        is_customer=False
    )
    
    print(f"Created vendor user: {vendor_user.username}")
    print(f"UUID: {vendor_user.id}")
    print(f"First name: {vendor_user.first_name}")
    print(f"Last name: {vendor_user.last_name}")
    
    # Create vendor profile
    vendor_profile = VendorProfile.objects.create(
        user=vendor_user,
        store_name="John's Store",
        description="A test vendor store",
        address="123 Vendor St",
        phone="555-VENDOR"
    )
    
    print(f"\nVendor Profile created: {vendor_profile.store_name}")
    print(f"Profile ID: {vendor_profile.id}")
    print(f"User ID: {vendor_profile.user.id}")
    print(f"User first name: {vendor_profile.user.first_name}")
    print(f"User last name: {vendor_profile.user.last_name}")
    
except Exception as e:
    print(f"Error creating vendor: {e}")

# Create a customer user directly with ORM
try:
    # Create customer user
    customer_user = User.objects.create_user(
        username='testcustomer',
        email='customer@example.com',
        password='password123',
        first_name='Jane',
        last_name='Buyer',
        is_vendor=False,
        is_customer=True
    )
    
    print(f"\nCreated customer user: {customer_user.username}")
    print(f"UUID: {customer_user.id}")
    print(f"First name: {customer_user.first_name}")
    print(f"Last name: {customer_user.last_name}")
    
    # Create customer profile
    customer_profile = CustomerProfile.objects.create(
        user=customer_user,
        address="456 Customer Ave",
        phone="555-CUSTOMER",
        preferences={"favorite_category": "electronics"}
    )
    
    print(f"\nCustomer Profile created: {customer_profile.user.username}")
    print(f"Profile ID: {customer_profile.id}")
    print(f"User ID: {customer_profile.user.id}")
    print(f"User first name: {customer_profile.user.first_name}")
    print(f"User last name: {customer_profile.user.last_name}")
    
except Exception as e:
    print(f"Error creating customer: {e}")

print("\nTest completed!")