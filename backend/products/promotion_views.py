from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal

from .models import FlashSale, BundleDeal, LoyaltyPoints, ReferralProgram, ProductBadge, Product
from .extended_serializers import (
    FlashSaleSerializer, BundleDealSerializer, LoyaltyPointsSerializer,
    ReferralProgramSerializer, ProductBadgeSerializer
)
from profiles.permissions import IsVendor


class FlashSaleViewSet(viewsets.ModelViewSet):
    """
    Flash Sale Management ViewSet
    
    Public Endpoints:
    - GET /api/products/flash-sales/ - List all active flash sales
    - GET /api/products/flash-sales/{id}/ - Get flash sale details
    - GET /api/products/flash-sales/live/ - Get currently live sales
    
    Vendor/Admin Endpoints:
    - POST /api/products/flash-sales/ - Create flash sale
    - PUT /api/products/flash-sales/{id}/ - Update flash sale
    - DELETE /api/products/flash-sales/{id}/ - Delete flash sale
    - POST /api/products/flash-sales/{id}/add_products/ - Add products to sale
    - POST /api/products/flash-sales/{id}/remove_products/ - Remove products
    """
    serializer_class = FlashSaleSerializer
    
    def get_permissions(self):
        """Allow public read, vendor/admin write"""
        if self.action in ['list', 'retrieve', 'live']:
            return [AllowAny()]
        return [IsVendor()]
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        
        # Public users see only active sales
        if not user.is_authenticated:
            return FlashSale.objects.filter(is_active=True)
        
        # Vendors see their own sales (if products belong to them)
        if hasattr(user, 'vendor_profile'):
            return FlashSale.objects.filter(
                Q(products__vendor=user.vendor_profile) | 
                Q(is_active=True)
            ).distinct()
        
        # Regular users see active sales
        return FlashSale.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def live(self, request):
        """Get all currently live flash sales"""
        now = timezone.now()
        live_sales = FlashSale.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        )
        
        serializer = self.get_serializer(live_sales, many=True)
        return Response({
            'count': live_sales.count(),
            'sales': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsVendor])
    def add_products(self, request, pk=None):
        """Add products to flash sale"""
        flash_sale = self.get_object()
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'detail': 'No product IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify vendor owns these products
        products = Product.objects.filter(
            id__in=product_ids,
            vendor=request.user.vendor_profile
        )
        
        if products.count() != len(product_ids):
            return Response(
                {'detail': 'Some products not found or not owned by you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        flash_sale.products.add(*products)
        
        return Response({
            'detail': f'Added {products.count()} products to flash sale',
            'total_products': flash_sale.products.count()
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsVendor])
    def remove_products(self, request, pk=None):
        """Remove products from flash sale"""
        flash_sale = self.get_object()
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'detail': 'No product IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = Product.objects.filter(id__in=product_ids)
        flash_sale.products.remove(*products)
        
        return Response({
            'detail': f'Removed {len(product_ids)} products from flash sale',
            'total_products': flash_sale.products.count()
        })
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def get_discounted_price(self, request, pk=None):
        """Calculate discounted price for a product"""
        flash_sale = self.get_object()
        product_id = request.query_params.get('product_id')
        
        if not product_id:
            return Response(
                {'detail': 'product_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Check if product is in this sale
            if not flash_sale.products.filter(id=product_id).exists():
                return Response(
                    {'detail': 'Product not in this flash sale'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate discounted price
            discount_multiplier = (100 - flash_sale.discount_percentage) / 100
            discounted_price = (product.price * discount_multiplier).quantize(Decimal('0.01'))
            savings = product.price - discounted_price
            
            return Response({
                'product_id': str(product.id),
                'product_name': product.name,
                'original_price': str(product.price),
                'discounted_price': str(discounted_price),
                'savings': str(savings),
                'discount_percentage': str(flash_sale.discount_percentage)
            })
            
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class BundleDealViewSet(viewsets.ModelViewSet):
    """
    Bundle Deal Management ViewSet
    
    Endpoints:
    - GET /api/products/bundles/ - List all active bundles
    - POST /api/products/bundles/ - Create bundle (vendor/admin)
    - GET /api/products/bundles/{id}/ - Get bundle details
    - PUT /api/products/bundles/{id}/ - Update bundle
    - DELETE /api/products/bundles/{id}/ - Delete bundle
    """
    serializer_class = BundleDealSerializer
    
    def get_permissions(self):
        """Allow public read, vendor/admin write"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsVendor()]
    
    def get_queryset(self):
        """Show active bundles"""
        now = timezone.now()
        return BundleDeal.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )


class LoyaltyPointsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Loyalty Points ViewSet
    
    Endpoints:
    - GET /api/products/loyalty-points/ - Get user's points history
    - GET /api/products/loyalty-points/balance/ - Get current balance
    """
    serializer_class = LoyaltyPointsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return user's loyalty points history"""
        return LoyaltyPoints.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get user's current loyalty points balance"""
        balance = LoyaltyPoints.get_user_balance(request.user)
        
        # Get recent transactions
        recent = LoyaltyPoints.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        return Response({
            'balance': balance,
            'recent_transactions': LoyaltyPointsSerializer(recent, many=True).data
        })


class ReferralProgramViewSet(viewsets.ModelViewSet):
    """
    Referral Program ViewSet
    
    Endpoints:
    - GET /api/products/referrals/ - Get user's referrals
    - POST /api/products/referrals/ - Create referral
    - GET /api/products/referrals/my_code/ - Get user's referral code
    - POST /api/products/referrals/apply/ - Apply referral code
    """
    serializer_class = ReferralProgramSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return user's referrals"""
        return ReferralProgram.objects.filter(referrer=self.request.user)
    
    def perform_create(self, serializer):
        """Create referral with auto-generated code"""
        import random
        import string
        
        # Generate unique referral code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        serializer.save(
            referrer=self.request.user,
            referral_code=code
        )
    
    @action(detail=False, methods=['get'])
    def my_code(self, request):
        """Get user's referral code"""
        # Get or create referral entry
        referral = ReferralProgram.objects.filter(referrer=request.user).first()
        
        if not referral:
            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            referral = ReferralProgram.objects.create(
                referrer=request.user,
                referral_code=code
            )
        
        return Response({
            'referral_code': referral.referral_code,
            'reward_points': referral.reward_points,
            'total_referrals': ReferralProgram.objects.filter(
                referrer=request.user,
                status='completed'
            ).count()
        })
    
    @action(detail=False, methods=['post'])
    def apply(self, request):
        """Apply a referral code when signing up"""
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'detail': 'Referral code required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            referral = ReferralProgram.objects.get(referral_code=code, status='pending')
            
            # Can't refer yourself
            if referral.referrer == request.user:
                return Response(
                    {'detail': 'Cannot use your own referral code'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark referral as completed
            referral.referred = request.user
            referral.status = 'completed'
            referral.completed_at = timezone.now()
            referral.save()
            
            # Award points to referrer
            LoyaltyPoints.objects.create(
                user=referral.referrer,
                points=referral.reward_points,
                transaction_type='earned',
                reference=f'referral-{code}',
                description=f'Referral reward for {request.user.username}'
            )
            
            # Award points to referred user
            LoyaltyPoints.objects.create(
                user=request.user,
                points=50,  # Welcome bonus
                transaction_type='earned',
                reference=f'referred-by-{code}',
                description='Welcome bonus for using referral code'
            )
            
            return Response({
                'detail': 'Referral code applied successfully',
                'reward_points': 50
            })
            
        except ReferralProgram.DoesNotExist:
            return Response(
                {'detail': 'Invalid or expired referral code'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductBadgeViewSet(viewsets.ModelViewSet):
    """
    Product Badge Management ViewSet (Vendor/Admin only)
    
    Endpoints:
    - GET /api/products/badges/ - List all badges
    - POST /api/products/badges/ - Add badge to product
    - DELETE /api/products/badges/{id}/ - Remove badge
    """
    serializer_class = ProductBadgeSerializer
    permission_classes = [IsVendor]
    
    def get_queryset(self):
        """Vendors see badges for their products"""
        if hasattr(self.request.user, 'vendor_profile'):
            return ProductBadge.objects.filter(
                product__vendor=self.request.user.vendor_profile
            )
        return ProductBadge.objects.all()
    
    def perform_create(self, serializer):
        """Add badge to product"""
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id)
        
        # Verify vendor owns product
        if product.vendor != self.request.user.vendor_profile:
            raise PermissionDenied("You can only add badges to your own products")
        
        serializer.save()

