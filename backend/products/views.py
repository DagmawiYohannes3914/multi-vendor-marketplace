from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg

from .models import Category, Product, ProductImage, SKU, InventoryTransaction, ProductRating
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, ProductSerializer, 
    ProductCreateUpdateSerializer, ProductImageSerializer, SKUSerializer,
    InventoryTransactionSerializer, ProductRatingSerializer
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
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsVendorAndOwner()]
    
    def get_queryset(self):
        # For list and retrieve actions, show all active products to everyone
        if self.action in ['list', 'retrieve']:
            if self.request.user.is_authenticated and hasattr(self.request.user, 'vendorprofile'):
                # Vendors see only their own products
                return Product.objects.filter(vendor=self.request.user.vendorprofile)
            # Public users see all active products
            return Product.objects.filter(is_active=True)
        
        # For other actions (create, update, delete), vendors only see their own products
        if self.request.user.is_authenticated and hasattr(self.request.user, 'vendorprofile'):
            return Product.objects.filter(vendor=self.request.user.vendorprofile)
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
        return ProductImage.objects.filter(product__vendor=self.request.user.vendorprofile)
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id, vendor=self.request.user.vendorprofile)
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
            if self.request.user.is_authenticated and hasattr(self.request.user, 'vendorprofile'):
                # Vendors see all SKUs for their products
                return SKU.objects.filter(product__vendor=self.request.user.vendorprofile)
            # Public users see all SKUs for active products
            return SKU.objects.filter(product__is_active=True)
        
        # For other actions, vendors only see SKUs for their own products
        if self.request.user.is_authenticated and hasattr(self.request.user, 'vendorprofile'):
            return SKU.objects.filter(product__vendor=self.request.user.vendorprofile)
        return SKU.objects.none()
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id, vendor=self.request.user.vendorprofile)
        serializer.save(product=product)

class InventoryTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventory transactions.
    """
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsVendorAndOwner]
    
    def get_queryset(self):
        return InventoryTransaction.objects.filter(sku__product__vendor=self.request.user.vendorprofile)
    
    def perform_create(self, serializer):
        sku_id = self.request.data.get('sku')
        sku = SKU.objects.get(id=sku_id, product__vendor=self.request.user.vendorprofile)
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
    
    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        
        # Check if user has already rated this product
        existing_rating = ProductRating.objects.filter(product=product, user=self.request.user).first()
        if existing_rating:
            return Response(
                {"detail": "You have already rated this product."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(product=product, user=self.request.user)
