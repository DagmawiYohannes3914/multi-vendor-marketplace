from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CheckoutView, StripeWebhookView, StripeConfigView, CouponViewSet, OrderViewSet
from .shipping_views import (
    ShippingAddressViewSet, ShippingRateViewSet, 
    OrderCancellationViewSet, ReturnRequestViewSet
)

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'coupons', CouponViewSet, basename='coupons')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')
router.register(r'shipping-rates', ShippingRateViewSet, basename='shipping-rate')
router.register(r'cancellations', OrderCancellationViewSet, basename='cancellation')
router.register(r'returns', ReturnRequestViewSet, basename='return')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payments/stripe/config/', StripeConfigView.as_view(), name='stripe-config'),
    path('payments/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]