from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorProfileView, CustomerProfileView, VendorReviewViewSet, PublicVendorProfileView
from .dashboard_views import VendorDashboardViewSet

router = DefaultRouter()
router.register(r'reviews', VendorReviewViewSet, basename='vendor-reviews')
router.register(r'vendor/dashboard', VendorDashboardViewSet, basename='vendor-dashboard')

urlpatterns = [
    path('vendor/', VendorProfileView.as_view(), name='vendor-profile'),
    path('vendor/<uuid:pk>/', PublicVendorProfileView.as_view(), name='public-vendor-profile'),
    path('customer/', CustomerProfileView.as_view(), name='customer-profile'),
    path('', include(router.urls)),
]