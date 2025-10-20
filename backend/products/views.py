from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg

from .models import Category, Product, ProductImage, SKU, InventoryTransaction, ProductRating, Wishlist, BulkDiscount, ProductComment
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, ProductSerializer, 
    ProductCreateUpdateSerializer, ProductImageSerializer, SKUSerializer,
    InventoryTransactionSerializer, ProductRatingSerializer, WishlistSerializer,
    BulkDiscountSerializer, ProductCommentSerializer
)
from .permissions import IsVendorAndOwner
from profiles.permissions import IsVendor, IsCustomer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing categories.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Return categories in a hierarchical tree structure.
        """
        root_categories = Category.objects.filter(parent=None, is_active=True)
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing products.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # For list and retrieve actions, show all active products to everyone
        if self.action in ['list', 'retrieve']:
            # Everyone (including vendors) see all active products for browsing
            return Product.objects.filter(is_active=True)
        
        # For other actions (create, update, delete), vendors only see their own products
        if self.request.user.is_authenticated and hasattr(self.request.user, 'vendor_profile'):
            return Product.objects.filter(vendor=self.request.user.vendor_profile)
        return Product.objects.none()
        
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsVendor]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsVendorAndOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

class ProductImageView(generics.CreateAPIView, generics.DestroyAPIView):
    """
    API endpoint for adding and removing product images.
    """
    serializer_class = ProductImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsVendorAndOwner]
    
    def get_queryset(self):
        return ProductImage.objects.filter(product__vendor=self.request.user.vendor_profile)
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id, vendor=self.request.user.vendor_profile)
        serializer.save(product=product)

class SKUViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product SKUs.
    """
    serializer_class = SKUSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsVendorAndOwner()]
    
    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            if self.request.user.is_authenticated and hasattr(self.request.user, 'vendor_profile'):
                # Vendors see all SKUs for their products
                return SKU.objects.filter(product__vendor=self.request.user.vendor_profile)
            # Public users see all SKUs for active products
            return SKU.objects.filter(product__is_active=True)
        
        # For other actions, vendors only see SKUs for their own products
        if self.request.user.is_authenticated and hasattr(self.request.user, 'vendor_profile'):
            return SKU.objects.filter(product__vendor=self.request.user.vendor_profile)
        return SKU.objects.none()
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id, vendor=self.request.user.vendor_profile)
        serializer.save(product=product)

class InventoryTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventory transactions.
    """
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsVendorAndOwner]
    
    def get_queryset(self):
        return InventoryTransaction.objects.filter(sku__product__vendor=self.request.user.vendor_profile)
    
    def perform_create(self, serializer):
        sku_id = self.request.data.get('sku')
        sku = SKU.objects.get(id=sku_id, product__vendor=self.request.user.vendor_profile)
        serializer.save(sku=sku, created_by=self.request.user)
        
        # Update the SKU stock quantity
        quantity = serializer.validated_data['quantity']
        sku.stock_quantity += quantity
        sku.save()

class ProductRatingView(generics.CreateAPIView, generics.ListAPIView):
    """
    API endpoint for rating products.
    """
    serializer_class = ProductRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductRating.objects.filter(product_id=product_id)
    
    def create(self, request, *args, **kwargs):
        """Override create to add validation before saving"""
        product_id = self.kwargs.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has already rated this product
        existing_rating = ProductRating.objects.filter(product=product, user=request.user).first()
        if existing_rating:
            return Response(
                {"detail": "You have already rated this product."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Continue with normal creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WishlistViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing wishlists.
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return wishlists for the current user only"""
        return Wishlist.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """Add a product to the wishlist"""
        wishlist = self.get_object()
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({"detail": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
            wishlist.products.add(product)
            return Response({"detail": "Product added to wishlist"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_product(self, request, pk=None):
        """Remove a product from the wishlist"""
        wishlist = self.get_object()
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({"detail": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
            wishlist.products.remove(product)
            return Response({"detail": "Product removed from wishlist"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


class BulkDiscountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing bulk discounts.
    """
    serializer_class = BulkDiscountSerializer
    permission_classes = [IsVendor]
    
    def get_queryset(self):
        """
        Return bulk discounts for the current vendor only, or all active discounts for customers
        """
        if hasattr(self.request.user, 'vendor_profile'):
            # Vendors see only their own discounts
            return BulkDiscount.objects.filter(vendor=self.request.user.vendor_profile)
        # Customers see all active discounts
        return BulkDiscount.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def vendor_discounts(self, request):
        """Return all active bulk discounts for a specific vendor"""
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response({"detail": "Vendor ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        discounts = BulkDiscount.objects.filter(vendor_id=vendor_id, is_active=True)
        serializer = self.get_serializer(discounts, many=True)
        return Response(serializer.data)


class ProductCommentViewSet(viewsets.ModelViewSet):
    serializer_class = ProductCommentSerializer
    queryset = ProductComment.objects.filter(is_approved=True)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']
    
    def get_permissions(self):
        if self.action in ['create']:
            return []  # Allow anyone to create comments (guests included)
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def product_comments(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        comments = ProductComment.objects.filter(product_id=product_id, is_approved=True)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)
