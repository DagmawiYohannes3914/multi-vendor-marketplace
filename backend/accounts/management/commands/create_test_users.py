# accounts/management/commands/create_test_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import VendorProfile, CustomerProfile
from django.db import connection

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test users with first and last names (vendor and customer)'

    def handle(self, *args, **options):
        # Display database connection info
        self.stdout.write(self.style.SUCCESS(f"Database engine: {connection.vendor}"))
        
        # Clean up existing test users
        User.objects.filter(username__in=['testvendor', 'testcustomer']).delete()
        
        # Create vendor user
        try:
            vendor_user = User.objects.create_user(
                username='testvendor',
                email='vendor@example.com',
                password='password123',
                first_name='John',
                last_name='Seller',
                is_vendor=True,
                is_customer=False
            )
            
            self.stdout.write(self.style.SUCCESS(f"Created vendor user: {vendor_user.username}"))
            self.stdout.write(f"UUID: {vendor_user.id}")
            self.stdout.write(f"First name: {vendor_user.first_name}")
            self.stdout.write(f"Last name: {vendor_user.last_name}")
            
            # Create vendor profile
            vendor_profile = VendorProfile.objects.create(
                user=vendor_user,
                store_name="John's Store",
                description="A test vendor store",
                address="123 Vendor St",
                phone="555-VENDOR"
            )
            
            self.stdout.write(self.style.SUCCESS(f"\nVendor Profile created: {vendor_profile.store_name}"))
            self.stdout.write(f"Profile ID: {vendor_profile.id}")
            self.stdout.write(f"User ID: {vendor_profile.user.id}")
            self.stdout.write(f"User first name: {vendor_profile.user.first_name}")
            self.stdout.write(f"User last name: {vendor_profile.user.last_name}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating vendor: {e}"))
            self.stdout.write(self.style.WARNING(f"Error type: {type(e).__name__}"))
            # Continue execution even if vendor creation fails

        # Create customer user
        try:
            customer_user = User.objects.create_user(
                username='testcustomer',
                email='customer@example.com',
                password='password123',
                first_name='Jane',
                last_name='Buyer',
                is_vendor=False,
                is_customer=True
            )
            
            self.stdout.write(self.style.SUCCESS(f"\nCreated customer user: {customer_user.username}"))
            self.stdout.write(f"UUID: {customer_user.id}")
            self.stdout.write(f"First name: {customer_user.first_name}")
            self.stdout.write(f"Last name: {customer_user.last_name}")
            
            # Create customer profile
            customer_profile = CustomerProfile.objects.create(
                user=customer_user,
                address="456 Customer Ave",
                phone="555-CUSTOMER",
                preferences={"favorite_category": "electronics"}
            )
            
            self.stdout.write(self.style.SUCCESS(f"\nCustomer Profile created: {customer_profile.user.username}"))
            self.stdout.write(f"Profile ID: {customer_profile.id}")
            self.stdout.write(f"User ID: {customer_profile.user.id}")
            self.stdout.write(f"User first name: {customer_profile.user.first_name}")
            self.stdout.write(f"User last name: {customer_profile.user.last_name}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating customer: {e}"))
            self.stdout.write(self.style.WARNING(f"Error type: {type(e).__name__}"))

        self.stdout.write(self.style.SUCCESS("\nTest users creation completed!"))