"""
Django Test Framework - Comprehensive System Test
Tests all implemented features
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from products.models import Product, SKU, Category, FlashSale, LoyaltyPoints
from orders.models import Order, VendorOrder, ShippingAddress
from profiles.models import VendorProfile, CustomerProfile

User = get_user_model()

@override_settings(ALLOWED_HOSTS=['*'])
class ComprehensiveSystemTest(APITestCase):
    def setUp(self):
        """Setup test users and data"""
        # Create vendor
        self.vendor_user = User.objects.create_user(
            username='test_vendor',
            email='vendor@test.com',
            password='testpass123',
            is_vendor=True,
            first_name='Test',
            last_name='Vendor'
        )
        self.vendor_profile, _ = VendorProfile.objects.get_or_create(
            user=self.vendor_user,
            defaults={'store_name': 'Test Store'}
        )
        
        # Create customer
        self.customer_user = User.objects.create_user(
            username='test_customer',
            email='customer@test.com',
            password='testpass123',
            is_customer=True,
            first_name='Test',
            last_name='Customer'
        )
        self.customer_profile, _ = CustomerProfile.objects.get_or_create(
            user=self.customer_user
        )
        
        # Get tokens
        self.vendor_token = str(RefreshToken.for_user(self.vendor_user).access_token)
        self.customer_token = str(RefreshToken.for_user(self.customer_user).access_token)
        
        # Create test product
        self.category, _ = Category.objects.get_or_create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product, _ = Product.objects.get_or_create(
            vendor=self.vendor_profile,
            category=self.category,
            name='Test Product',
            slug='test-product',
            price=Decimal('99.99'),
            defaults={'is_active': True}
        )
        
        self.sku, _ = SKU.objects.get_or_create(
            product=self.product,
            sku_code='TEST-SKU-001',
            defaults={'stock_quantity': 100}
        )
    
    def test_shipping_addresses(self):
        """Test shipping address CRUD"""
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
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        
        self.assertEqual(response.status_code, 201, f"Create address failed: {response.data}")
        address_id = response.data['id']
        
        # List addresses
        response = self.client.get(
            '/api/orders/shipping-addresses/',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        
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
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['label'], 'Home Updated')
    
    def test_reviews_and_voting(self):
        """Test review system with voting"""
        # Create review
        response = self.client.post(
            '/api/products/ratings/',
            {
                'product': str(self.product.id),
                'rating': 5,
                'review': 'Excellent product!'
            },
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        
        self.assertEqual(response.status_code, 201, f"Create review failed: {response.data}")
        rating_id = response.data['id']
        
        # Vote on review (using vendor account)
        response = self.client.post(
            f'/api/products/ratings/{rating_id}/vote/',
            {'vote_type': 'helpful'},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['helpful_votes'], 1)
    
    def test_product_qa(self):
        """Test Product Q&A system"""
        # Ask question
        response = self.client.post(
            '/api/products/questions/',
            {
                'product': str(self.product.id),
                'question': 'What is the warranty period?'
            },
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        
        self.assertEqual(response.status_code, 201, f"Ask question failed: {response.data}")
        question_id = response.data['id']
        
        # Answer question (vendor)
        response = self.client.post(
            '/api/products/answers/',
            {
                'question': question_id,
                'answer': 'The warranty period is 1 year.'
            },
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        
        self.assertEqual(response.status_code, 201, f"Answer question failed: {response.data}")
        self.assertTrue(response.data['is_vendor'])
    
    def test_flash_sales(self):
        """Test flash sales"""
        # Create flash sale
        now = timezone.now()
        flash_sale = FlashSale.objects.create(
            name='Test Flash Sale',
            description='Test sale',
            discount_percentage=Decimal('50.00'),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            max_quantity_per_user=5,
            is_active=True
        )
        flash_sale.products.add(self.product)
        
        # Get live flash sales
        response = self.client.get('/api/products/flash-sales/live/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        
        # Get discounted price
        response = self.client.get(
            f'/api/products/flash-sales/{flash_sale.id}/get_discounted_price/?product_id={self.product.id}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(response.data['discounted_price']), 49.99)
    
    def test_loyalty_points(self):
        """Test loyalty points"""
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
        
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['balance'], 100)
    
    def test_referral_program(self):
        """Test referral program"""
        # Get referral code
        response = self.client.get(
            '/api/products/referrals/my_code/',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('referral_code', response.data)
    
    def test_vendor_dashboard(self):
        """Test vendor dashboard"""
        # Get dashboard stats
        response = self.client.get(
            '/api/profiles/vendor/dashboard/stats/',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        
        self.assertEqual(response.status_code, 200, f"Dashboard stats failed: {response.data}")
        self.assertIn('total_products', response.data)
        
        # Get vendor orders
        response = self.client.get(
            '/api/profiles/vendor/dashboard/orders/',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        self.assertEqual(response.status_code, 200)
        
        # Get product performance
        response = self.client.get(
            '/api/profiles/vendor/dashboard/product_performance/',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        self.assertEqual(response.status_code, 200)
        
        # Get low stock alerts
        response = self.client.get(
            '/api/profiles/vendor/dashboard/low_stock_alerts/',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        self.assertEqual(response.status_code, 200)
        
        # Get revenue report
        response = self.client.get(
            '/api/profiles/vendor/dashboard/revenue_report/',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_returns_system(self):
        """Test returns/refunds system"""
        # Create a test order first
        order = Order.objects.create(
            user=self.customer_user,
            status='delivered',
            total_amount=Decimal('99.99'),
            subtotal_amount=Decimal('99.99'),
            payment_method='stripe',
            shipping_address={'street': '123 Test St'}
        )
        
        vendor_order = VendorOrder.objects.create(
            order=order,
            vendor=self.vendor_profile,
            status='delivered',
            total_amount=Decimal('99.99')
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
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.customer_token}'
        )
        
        self.assertEqual(response.status_code, 201, f"Create return failed: {response.data}")
        return_id = response.data['id']
        
        # Vendor approves return
        response = self.client.post(
            f'/api/orders/returns/{return_id}/approve/',
            {'notes': 'Approved'},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.vendor_token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['return']['status'], 'approved')


if __name__ == '__main__':
    from django.test.runner import DiscoverRunner
    
    print("="*80)
    print("🧪 COMPREHENSIVE SYSTEM TEST".center(80))
    print("="*80)
    
    runner = DiscoverRunner(verbosity=2)
    test_suite = runner.test_loader.loadTestsFromTestCase(ComprehensiveSystemTest)
    test_runner = runner.run_suite(test_suite)
    
    print("\n" + "="*80)
    print("📊 TEST RESULTS".center(80))
    print("="*80)
    print(f"\n✅ Tests run: {test_runner.testsRun}")
    print(f"✅ Passed: {test_runner.testsRun - len(test_runner.failures) - len(test_runner.errors)}")
    print(f"❌ Failed: {len(test_runner.failures)}")
    print(f"❌ Errors: {len(test_runner.errors)}")
    
    if test_runner.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print("\n⚠️ SOME TESTS FAILED")
    
    print("="*80)

