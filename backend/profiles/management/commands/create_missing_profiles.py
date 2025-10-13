from django.core.management.base import BaseCommand
from accounts.models import User
from profiles.models import VendorProfile, CustomerProfile


class Command(BaseCommand):
    help = 'Creates missing vendor and customer profiles for users with both flags'

    def handle(self, *args, **options):
        users_with_both_flags = User.objects.filter(is_vendor=True, is_customer=True)
        self.stdout.write(f'Found {users_with_both_flags.count()} users with both flags')
        
        for user in users_with_both_flags:
            vendor_exists = VendorProfile.objects.filter(user=user).exists()
            customer_exists = CustomerProfile.objects.filter(user=user).exists()
            
            if not vendor_exists:
                VendorProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created vendor profile for {user.username}'))
            
            if not customer_exists:
                CustomerProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created customer profile for {user.username}'))
            
            self.stdout.write(f'User: {user.username}, Vendor: {vendor_exists}, Customer: {customer_exists}')
        
        self.stdout.write(self.style.SUCCESS('Profile creation completed'))