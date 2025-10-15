from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'skus', views.SKUViewSet, basename='sku')
router.register(r'inventory', views.InventoryTransactionViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
    path('product-images/', views.ProductImageView.as_view(), name='product-images'),
    path('products/<int:product_id>/ratings/', views.ProductRatingView.as_view(), name='product-ratings'),
]