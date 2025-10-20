"""
Comprehensive System Test
Tests all features including new implementations
"""
import os
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import (
    Product, SKU, Category, ProductRating, ReviewImage, ReviewVote,
    ProductQuestion, ProductAnswer, FlashSale, BundleDeal, 
    LoyaltyPoints, ReferralProgram, ProductBadge
)
from orders.models import (
    Order, VendorOrder, OrderItem, Cart, CartItem,
    ShippingAddress, ShippingRate, ReturnRequest, OrderCancellation
)
from profiles.models import VendorProfile, CustomerProfile

User = get_user_model()

class SystemTester:
    def __init__(self):
        self.client = Client()
        self.errors = []
        self.passed = []
        self.vendor_user = None
        self.customer_user = None
        self.vendor_token = None
        self.customer_token = None
        
    def log_error(self, test_name, error):
        self.errors.append(f"❌ {test_name}: {error}")
        
    def log_pass(self, test_name):
        self.passed.append(f"✅ {test_name}")
        
    def setup_test_users(self):
        """Setup test users"""
        print("\n📋 Setting up test users...")
        try:
            # Create vendor
            self.vendor_user, created = User.objects.get_or_create(
                username='test_vendor',
                defaults={
                    'email': 'vendor@test.com',
                    'is_vendor': True,
                    'first_name': 'Test',
                    'last_name': 'Vendor'
                }
            )
            if created:
                self.vendor_user.set_password('testpass123')
                self.vendor_user.save()
                VendorProfile.objects.get_or_create(
                    user=self.vendor_user,
                    defaults={'store_name': 'Test Store'}
                )
            
            # Create customer
            self.customer_user, created = User.objects.get_or_create(
                username='test_customer',
                defaults={
                    'email': 'customer@test.com',
                    'is_customer': True,
                    'first_name': 'Test',
                    'last_name': 'Customer'
                }
            )
            if created:
                self.customer_user.set_password('testpass123')
                self.customer_user.save()
                CustomerProfile.objects.get_or_create(user=self.customer_user)
            
            # Get tokens
            self.vendor_token = str(RefreshToken.for_user(self.vendor_user).access_token)
            self.customer_token = str(RefreshToken.for_user(self.customer_user).access_token)
            
            self.log_pass("User setup")
            return True
        except Exception as e:
            self.log_error("User setup", str(e))
            return False
    
    def test_shipping_addresses(self):
        """Test shipping address CRUD"""
        print("\n🚚 Testing Shipping Addresses...")
        try:
            # Create address
            response = self.client.post(
                '/api/orders/shipping-addresses/',
                {
                    'label': 'Home',
                    'recipient_name': 'Test Customer',
                    'phone': '+1234567890',
                    'street_address': '123 Test St',
                    'city': 'Test City',
                    'state': 'TS',
                    'postal_code': '12345',
                    'country': 'USA',
                    'is_default': True
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 201:
                self.log_error("Create shipping address", f"Status {response.status_code}: {response.json()}")
                return False
            
            address_id = response.json()['id']
            
            # List addresses
            response = self.client.get(
                '/api/orders/shipping-addresses/',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 200:
                self.log_error("List shipping addresses", f"Status {response.status_code}")
                return False
            
            # Update address
            response = self.client.put(
                f'/api/orders/shipping-addresses/{address_id}/',
                {
                    'label': 'Home Updated',
                    'recipient_name': 'Test Customer',
                    'phone': '+1234567890',
                    'street_address': '123 Test St',
                    'city': 'Test City',
                    'state': 'TS',
                    'postal_code': '12345',
                    'country': 'USA',
                    'is_default': True
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Update shipping address", f"Status {response.status_code}")
                return False
            
            # Set as default
            response = self.client.post(
                f'/api/orders/shipping-addresses/{address_id}/set_default/',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Set default address", f"Status {response.status_code}")
                return False
            
            self.log_pass("Shipping addresses CRUD")
            return True
            
        except Exception as e:
            self.log_error("Shipping addresses", str(e))
            return False
    
    def test_reviews_and_voting(self):
        """Test review system with voting"""
        print("\n⭐ Testing Reviews & Voting...")
        try:
            # Create a product first
            category, _ = Category.objects.get_or_create(
                name='Test Category',
                slug='test-category'
            )
            
            product, _ = Product.objects.get_or_create(
                vendor=self.vendor_user.vendor_profile,
                category=category,
                name='Test Product',
                slug='test-product',
                price=Decimal('99.99'),
                defaults={'is_active': True}
            )
            
            # Create review
            response = self.client.post(
                '/api/products/ratings/',
                {
                    'product': str(product.id),
                    'rating': 5,
                    'review': 'Excellent product!'
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 201:
                self.log_error("Create review", f"Status {response.status_code}: {response.json()}")
                return False
            
            rating_id = response.json()['id']
            
            # Vote on review (using vendor account)
            response = self.client.post(
                f'/api/products/ratings/{rating_id}/vote/',
                {'vote_type': 'helpful'},
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Vote on review", f"Status {response.status_code}: {response.json()}")
                return False
            
            # List reviews
            response = self.client.get(
                f'/api/products/ratings/?product_id={product.id}'
            )
            
            if response.status_code != 200:
                self.log_error("List reviews", f"Status {response.status_code}")
                return False
            
            self.log_pass("Reviews & voting system")
            return True
            
        except Exception as e:
            self.log_error("Reviews system", str(e))
            return False
    
    def test_product_qa(self):
        """Test Product Q&A system"""
        print("\n❓ Testing Product Q&A...")
        try:
            # Get or create product
            category, _ = Category.objects.get_or_create(
                name='Test Category',
                slug='test-category'
            )
            
            product, _ = Product.objects.get_or_create(
                vendor=self.vendor_user.vendor_profile,
                category=category,
                name='Test Product',
                slug='test-product',
                price=Decimal('99.99'),
                defaults={'is_active': True}
            )
            
            # Ask question
            response = self.client.post(
                '/api/products/questions/',
                {
                    'product': str(product.id),
                    'question': 'What is the warranty period?'
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 201:
                self.log_error("Ask question", f"Status {response.status_code}: {response.json()}")
                return False
            
            question_id = response.json()['id']
            
            # Answer question (vendor)
            response = self.client.post(
                '/api/products/answers/',
                {
                    'question': question_id,
                    'answer': 'The warranty period is 1 year.'
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 201:
                self.log_error("Answer question", f"Status {response.status_code}: {response.json()}")
                return False
            
            # Get product Q&A
            response = self.client.get(
                f'/api/products/products/{product.id}/qa/'
            )
            
            if response.status_code != 200:
                self.log_error("Get product Q&A", f"Status {response.status_code}")
                return False
            
            self.log_pass("Product Q&A system")
            return True
            
        except Exception as e:
            self.log_error("Product Q&A", str(e))
            return False
    
    def test_flash_sales(self):
        """Test flash sales"""
        print("\n🔥 Testing Flash Sales...")
        try:
            # Get or create product
            category, _ = Category.objects.get_or_create(
                name='Test Category',
                slug='test-category'
            )
            
            product, _ = Product.objects.get_or_create(
                vendor=self.vendor_user.vendor_profile,
                category=category,
                name='Test Product',
                slug='test-product',
                price=Decimal('99.99'),
                defaults={'is_active': True}
            )
            
            # Create flash sale
            now = timezone.now()
            flash_sale, _ = FlashSale.objects.get_or_create(
                name='Test Flash Sale',
                defaults={
                    'description': 'Test sale',
                    'discount_percentage': Decimal('50.00'),
                    'start_time': now - timedelta(hours=1),
                    'end_time': now + timedelta(hours=1),
                    'max_quantity_per_user': 5,
                    'is_active': True
                }
            )
            flash_sale.products.add(product)
            
            # Get live flash sales
            response = self.client.get('/api/products/flash-sales/live/')
            
            if response.status_code != 200:
                self.log_error("Get live flash sales", f"Status {response.status_code}")
                return False
            
            # Get discounted price
            response = self.client.get(
                f'/api/products/flash-sales/{flash_sale.id}/get_discounted_price/?product_id={product.id}'
            )
            
            if response.status_code != 200:
                self.log_error("Get discounted price", f"Status {response.status_code}")
                return False
            
            data = response.json()
            if float(data['discounted_price']) != 49.99:
                self.log_error("Flash sale discount calculation", f"Expected 49.99, got {data['discounted_price']}")
                return False
            
            self.log_pass("Flash sales system")
            return True
            
        except Exception as e:
            self.log_error("Flash sales", str(e))
            return False
    
    def test_loyalty_points(self):
        """Test loyalty points"""
        print("\n🎁 Testing Loyalty Points...")
        try:
            # Create loyalty points
            LoyaltyPoints.objects.create(
                user=self.customer_user,
                points=100,
                transaction_type='earned',
                reference='test-order-123',
                description='Test purchase'
            )
            
            # Get balance
            response = self.client.get(
                '/api/products/loyalty-points/balance/',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Get loyalty points balance", f"Status {response.status_code}")
                return False
            
            data = response.json()
            if data['balance'] < 100:
                self.log_error("Loyalty points balance", f"Expected >= 100, got {data['balance']}")
                return False
            
            self.log_pass("Loyalty points system")
            return True
            
        except Exception as e:
            self.log_error("Loyalty points", str(e))
            return False
    
    def test_referral_program(self):
        """Test referral program"""
        print("\n🤝 Testing Referral Program...")
        try:
            # Get referral code
            response = self.client.get(
                '/api/products/referrals/my_code/',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Get referral code", f"Status {response.status_code}")
                return False
            
            self.log_pass("Referral program")
            return True
            
        except Exception as e:
            self.log_error("Referral program", str(e))
            return False
    
    def test_vendor_dashboard(self):
        """Test vendor dashboard"""
        print("\n📊 Testing Vendor Dashboard...")
        try:
            # Get dashboard stats
            response = self.client.get(
                '/api/profiles/vendor/dashboard/stats/',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Vendor dashboard stats", f"Status {response.status_code}: {response.json()}")
                return False
            
            # Get vendor orders
            response = self.client.get(
                '/api/profiles/vendor/dashboard/orders/',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Vendor dashboard orders", f"Status {response.status_code}")
                return False
            
            # Get product performance
            response = self.client.get(
                '/api/profiles/vendor/dashboard/product_performance/',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Vendor product performance", f"Status {response.status_code}")
                return False
            
            # Get low stock alerts
            response = self.client.get(
                '/api/profiles/vendor/dashboard/low_stock_alerts/',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Vendor low stock alerts", f"Status {response.status_code}")
                return False
            
            # Get revenue report
            response = self.client.get(
                '/api/profiles/vendor/dashboard/revenue_report/',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Vendor revenue report", f"Status {response.status_code}")
                return False
            
            self.log_pass("Vendor dashboard (all 5 endpoints)")
            return True
            
        except Exception as e:
            self.log_error("Vendor dashboard", str(e))
            return False
    
    def test_returns_system(self):
        """Test returns/refunds system"""
        print("\n↩️  Testing Returns System...")
        try:
            # Create a test order first
            order, _ = Order.objects.get_or_create(
                user=self.customer_user,
                defaults={
                    'status': 'delivered',
                    'total_amount': Decimal('99.99'),
                    'subtotal_amount': Decimal('99.99'),
                    'payment_method': 'stripe',
                    'shipping_address': {'street': '123 Test St'}
                }
            )
            
            vendor_order, _ = VendorOrder.objects.get_or_create(
                order=order,
                vendor=self.vendor_user.vendor_profile,
                defaults={
                    'status': 'delivered',
                    'total_amount': Decimal('99.99')
                }
            )
            
            # Create return request
            response = self.client.post(
                '/api/orders/returns/',
                {
                    'order': str(order.id),
                    'vendor_order': str(vendor_order.id),
                    'reason': 'defective',
                    'description': 'Product is defective'
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 201:
                self.log_error("Create return request", f"Status {response.status_code}: {response.json()}")
                return False
            
            return_id = response.json()['id']
            
            # List returns
            response = self.client.get(
                '/api/orders/returns/',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            
            if response.status_code != 200:
                self.log_error("List returns", f"Status {response.status_code}")
                return False
            
            # Vendor approves return
            response = self.client.post(
                f'/api/orders/returns/{return_id}/approve/',
                {'notes': 'Approved'},
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
            )
            
            if response.status_code != 200:
                self.log_error("Approve return", f"Status {response.status_code}: {response.json()}")
                return False
            
            self.log_pass("Returns/refunds system")
            return True
            
        except Exception as e:
            self.log_error("Returns system", str(e))
            return False
    
    def test_basic_features(self):
        """Test basic e-commerce features"""
        print("\n🛒 Testing Basic Features...")
        try:
            # Get products
            response = self.client.get('/api/products/products/')
            if response.status_code != 200:
                self.log_error("List products", f"Status {response.status_code}")
                return False
            
            # Get categories
            response = self.client.get('/api/products/categories/')
            if response.status_code != 200:
                self.log_error("List categories", f"Status {response.status_code}")
                return False
            
            # Get cart
            response = self.client.get(
                '/api/orders/cart/',
                HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
            )
            if response.status_code != 200:
                self.log_error("Get cart", f"Status {response.status_code}")
                return False
            
            self.log_pass("Basic features (products, categories, cart)")
            return True
            
        except Exception as e:
            self.log_error("Basic features", str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*80)
        print("🧪 COMPREHENSIVE SYSTEM TEST".center(80))
        print("="*80)
        
        # Setup
        if not self.setup_test_users():
            print("\n❌ Failed to setup test users. Aborting tests.")
            return
        
        # Run tests
        self.test_basic_features()
        self.test_shipping_addresses()
        self.test_reviews_and_voting()
        self.test_product_qa()
        self.test_flash_sales()
        self.test_loyalty_points()
        self.test_referral_program()
        self.test_vendor_dashboard()
        self.test_returns_system()
        
        # Print results
        print("\n" + "="*80)
        print("📊 TEST RESULTS".center(80))
        print("="*80)
        
        print(f"\n✅ PASSED: {len(self.passed)}")
        for test in self.passed:
            print(f"   {test}")
        
        if self.errors:
            print(f"\n❌ FAILED: {len(self.errors)}")
            for error in self.errors:
                print(f"   {error}")
        else:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        
        print("\n" + "="*80)
        print(f"Total: {len(self.passed)} passed, {len(self.errors)} failed")
        print("="*80)


if __name__ == '__main__':
    tester = SystemTester()
    tester.run_all_tests()

