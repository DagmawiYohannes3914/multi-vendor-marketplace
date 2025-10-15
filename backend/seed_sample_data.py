#!/usr/bin/env python
"""
Management command to seed sample data for the marketplace
including multiple products, SKUs, and ratings
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from profiles.models import VendorProfile, CustomerProfile
from products.models import Category, Product, SKU, ProductRating
import random
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds sample data for the marketplace including products, SKUs, and ratings'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...')
        
        # Get or create vendor users
        vendor1, _ = User.objects.get_or_create(
            username='vendor1',
            defaults={
                'email': 'vendor1@example.com',
                'is_active': True,
            }
        )
        vendor1.set_password('password123')
        vendor1.save()
        
        vendor2, _ = User.objects.get_or_create(
            username='vendor2',
            defaults={
                'email': 'vendor2@example.com',
                'is_active': True,
            }
        )
        vendor2.set_password('password123')
        vendor2.save()
        
        # Get or create customer users
        customer1, _ = User.objects.get_or_create(
            username='customer1',
            defaults={
                'email': 'customer1@example.com',
                'is_active': True,
            }
        )
        customer1.set_password('password123')
        customer1.save()
        
        customer2, _ = User.objects.get_or_create(
            username='customer2',
            defaults={
                'email': 'customer2@example.com',
                'is_active': True,
            }
        )
        customer2.set_password('password123')
        customer2.save()
        
        # Get or create vendor profiles
        vendor1_profile, _ = VendorProfile.objects.get_or_create(
            user=vendor1,
            defaults={
                'store_name': 'Tech Gadgets Store',
                'store_description': 'The best tech gadgets in town',
                'is_active': True,
            }
        )
        
        vendor2_profile, _ = VendorProfile.objects.get_or_create(
            user=vendor2,
            defaults={
                'store_name': 'Home & Living',
                'store_description': 'Quality products for your home',
                'is_active': True,
            }
        )
        
        # Get or create customer profiles
        customer1_profile, _ = CustomerProfile.objects.get_or_create(
            user=customer1,
            defaults={
                'shipping_address': '123 Main St, City',
                'preferences': {'notifications': True},
            }
        )
        
        customer2_profile, _ = CustomerProfile.objects.get_or_create(
            user=customer2,
            defaults={
                'shipping_address': '456 Oak Ave, Town',
                'preferences': {'notifications': False},
            }
        )
        
        # Create categories
        categories = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Home Appliances', 'description': 'Appliances for your home'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'description': 'Books and literature'},
            {'name': 'Sports', 'description': 'Sports equipment and gear'},
        ]
        
        created_categories = []
        for cat_data in categories:
            slug = slugify(cat_data['name'])
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'is_active': True,
                }
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f"Created category: {category.name}")
            else:
                self.stdout.write(f"Using existing category: {category.name}")
        
        # Create products
        products_data = [
            {
                'name': 'Smartphone X',
                'description': 'Latest smartphone with advanced features',
                'price': '999.99',
                'compare_price': '1099.99',
                'category': created_categories[0],  # Electronics
                'vendor': vendor1_profile,
                'is_featured': True,
            },
            {
                'name': 'Laptop Pro',
                'description': 'Powerful laptop for professionals',
                'price': '1499.99',
                'compare_price': '1699.99',
                'category': created_categories[0],  # Electronics
                'vendor': vendor1_profile,
                'is_featured': True,
            },
            {
                'name': 'Vacuum Z',
                'description': 'High-powered vacuum cleaner',
                'price': '199.99',
                'compare_price': '249.99',
                'category': created_categories[1],  # Home Appliances
                'vendor': vendor2_profile,
                'is_featured': False,
            },
            {
                'name': 'Coffee Maker Deluxe',
                'description': 'Premium coffee maker with timer',
                'price': '89.99',
                'compare_price': '119.99',
                'category': created_categories[1],  # Home Appliances
                'vendor': vendor2_profile,
                'is_featured': True,
            },
            {
                'name': 'Designer Jeans',
                'description': 'Stylish jeans for all occasions',
                'price': '79.99',
                'compare_price': '99.99',
                'category': created_categories[2],  # Clothing
                'vendor': vendor2_profile,
                'is_featured': False,
            },
            {
                'name': 'Programming Guide',
                'description': 'Comprehensive programming book',
                'price': '49.99',
                'compare_price': '59.99',
                'category': created_categories[3],  # Books
                'vendor': vendor1_profile,
                'is_featured': False,
            },
            {
                'name': 'Basketball',
                'description': 'Professional basketball',
                'price': '29.99',
                'compare_price': '39.99',
                'category': created_categories[4],  # Sports
                'vendor': vendor2_profile,
                'is_featured': False,
            },
        ]
        
        created_products = []
        for prod_data in products_data:
            slug = slugify(prod_data['name'])
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': prod_data['name'],
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'compare_price': prod_data['compare_price'],
                    'category': prod_data['category'],
                    'vendor': prod_data['vendor'],
                    'is_featured': prod_data['is_featured'],
                    'is_active': True,
                }
            )
            created_products.append(product)
            if created:
                self.stdout.write(f"Created product: {product.name}")
            else:
                self.stdout.write(f"Using existing product: {product.name}")
        
        # Create SKUs for products
        for product in created_products:
            # Create 2-3 SKUs per product
            num_skus = random.randint(2, 3)
            for i in range(num_skus):
                # Different attributes based on product category
                if product.category.name == 'Electronics':
                    attributes = {'color': random.choice(['Black', 'Silver', 'Gold']), 
                                 'storage': random.choice(['64GB', '128GB', '256GB'])}
                elif product.category.name == 'Clothing':
                    attributes = {'size': random.choice(['S', 'M', 'L', 'XL']), 
                                 'color': random.choice(['Blue', 'Black', 'Red', 'White'])}
                elif product.category.name == 'Home Appliances':
                    attributes = {'color': random.choice(['White', 'Black', 'Silver']), 
                                 'voltage': random.choice(['110V', '220V'])}
                elif product.category.name == 'Books':
                    attributes = {'format': random.choice(['Hardcover', 'Paperback', 'Digital'])}
                elif product.category.name == 'Sports':
                    attributes = {'size': random.choice(['Small', 'Medium', 'Large']), 
                                 'color': random.choice(['Orange', 'Blue', 'Black'])}
                else:
                    attributes = {'variant': f'Variant {i+1}'}
                
                # Generate a unique SKU code
                sku_code = f"{product.slug[:3].upper()}-{str(uuid.uuid4())[:8]}"
                
                # Price adjustment based on attributes
                price_adj = random.choice([-10.00, 0.00, 15.00, 25.00])
                
                # Random stock quantity
                stock_qty = random.randint(5, 100)
                
                sku, created = SKU.objects.get_or_create(
                    sku_code=sku_code,
                    defaults={
                        'product': product,
                        'attributes': attributes,
                        'price_adjustment': price_adj,
                        'stock_quantity': stock_qty,
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(f"Created SKU: {sku.sku_code} for {product.name} with attributes {attributes}")
        
        # Create ratings for products
        customers = [customer1, customer2]
        
        for product in created_products:
            # Add 1-2 ratings per product
            for customer in customers:
                if random.random() > 0.3:  # 70% chance to add a rating
                    rating_value = random.randint(3, 5)  # Mostly positive ratings
                    review_texts = [
                        "Great product, very satisfied!",
                        "Works as expected, good value.",
                        "Excellent quality, would recommend.",
                        "Shipped quickly and works well.",
                        "Very happy with my purchase."
                    ]
                    
                    rating, created = ProductRating.objects.get_or_create(
                        product=product,
                        user=customer,
                        defaults={
                            'rating': rating_value,
                            'review': random.choice(review_texts),
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"Created {rating_value}-star rating for {product.name} by {customer.username}")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded sample data!'))