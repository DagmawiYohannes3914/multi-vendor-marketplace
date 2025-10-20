from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .review_views import ProductRatingViewSet, ProductQuestionViewSet, ProductAnswerViewSet, ProductQAListView
from .promotion_views import (
    FlashSaleViewSet, BundleDealViewSet, LoyaltyPointsViewSet,
    ReferralProgramViewSet, ProductBadgeViewSet
)

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'skus', views.SKUViewSet, basename='sku')
router.register(r'inventory', views.InventoryTransactionViewSet, basename='inventory')
router.register(r'wishlists', views.WishlistViewSet, basename='wishlist')
router.register(r'bulk-discounts', views.BulkDiscountViewSet, basename='bulk-discount')
router.register(r'comments', views.ProductCommentViewSet, basename='product-comment')

# Review & Q&A
router.register(r'ratings', ProductRatingViewSet, basename='rating')
router.register(r'questions', ProductQuestionViewSet, basename='question')
router.register(r'answers', ProductAnswerViewSet, basename='answer')

# Promotions & Marketing
router.register(r'flash-sales', FlashSaleViewSet, basename='flash-sale')
router.register(r'bundles', BundleDealViewSet, basename='bundle')
router.register(r'loyalty-points', LoyaltyPointsViewSet, basename='loyalty-points')
router.register(r'referrals', ReferralProgramViewSet, basename='referral')
router.register(r'badges', ProductBadgeViewSet, basename='badge')

urlpatterns = [
    path('', include(router.urls)),
    path('product-images/', views.ProductImageView.as_view(), name='product-images'),
    path('products/<uuid:product_id>/qa/', ProductQAListView.as_view(), name='product-qa'),
]