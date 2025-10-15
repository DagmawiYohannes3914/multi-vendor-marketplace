from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import VendorProfile, CustomerProfile
from products.models import Category, Product
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Seed demo data: two users (vendor and customer), a category, and a product"

    def handle(self, *args, **options):
        User = get_user_model()

        # Create or get vendor user
        vendor_username = "vendor1"
        vendor_email = "vendor1@example.com"
        vendor_password = "Vendor123!"

        vendor_user, created_vendor = User.objects.get_or_create(
            username=vendor_username,
            defaults={
                "email": vendor_email,
                "is_vendor": True,
                "is_customer": False,
            },
        )
        if created_vendor:
            vendor_user.set_password(vendor_password)
            vendor_user.save(update_fields=["password"])
        else:
            # Ensure flags are correct
            update = False
            if not vendor_user.is_vendor:
                vendor_user.is_vendor = True
                update = True
            if vendor_user.is_customer:
                vendor_user.is_customer = False
                update = True
            if update:
                vendor_user.save(update_fields=["is_vendor", "is_customer"])

        # Create or get customer user
        customer_username = "customer1"
        customer_email = "customer1@example.com"
        customer_password = "Customer123!"

        customer_user, created_customer = User.objects.get_or_create(
            username=customer_username,
            defaults={
                "email": customer_email,
                "is_vendor": False,
                "is_customer": True,
            },
        )
        if created_customer:
            customer_user.set_password(customer_password)
            customer_user.save(update_fields=["password"])
        else:
            # Ensure flags are correct
            update = False
            if customer_user.is_vendor:
                customer_user.is_vendor = False
                update = True
            if not customer_user.is_customer:
                customer_user.is_customer = True
                update = True
            if update:
                customer_user.save(update_fields=["is_vendor", "is_customer"])

        # Create or get vendor profile
        vendor_profile, _ = VendorProfile.objects.get_or_create(
            user=vendor_user,
            defaults={
                "store_name": "Vendor One Store",
                "description": "Demo vendor store",
                "address": "123 Vendor St",
                "phone": "+1234567890",
            },
        )

        # Create or get customer profile
        customer_profile, _ = CustomerProfile.objects.get_or_create(
            user=customer_user,
            defaults={
                "address": "456 Customer Ave",
                "phone": "+0987654321",
                "preferences": {},
            },
        )

        # Create or get category
        category_name = "Electronics"
        category_slug = slugify(category_name)
        category, _ = Category.objects.get_or_create(
            slug=category_slug,
            defaults={
                "name": category_name,
                "description": "Electronic devices",
                "is_active": True,
            },
        )

        # Create or get product under the category
        product_name = "Smartphone X"
        product_slug = slugify(product_name)
        product, _ = Product.objects.get_or_create(
            slug=product_slug,
            defaults={
                "vendor": vendor_profile,
                "category": category,
                "name": product_name,
                "description": "A demo smartphone product",
                "price": "499.99",
                "compare_price": "549.99",
                "is_active": True,
                "is_featured": False,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded demo data successfully"))
        self.stdout.write(
            f"Vendor user: {vendor_user.username} (id={vendor_user.id}) | password={vendor_password}"
        )
        self.stdout.write(
            f"Customer user: {customer_user.username} (id={customer_user.id}) | password={customer_password}"
        )
        self.stdout.write(
            f"Category: {category.name} (id={category.id}), Product: {product.name} (id={product.id})"
        )