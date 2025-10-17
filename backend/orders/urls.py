from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CheckoutView, StripeWebhookView, StripeConfigView, CouponViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'coupons', CouponViewSet, basename='coupons')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payments/stripe/config/', StripeConfigView.as_view(), name='stripe-config'),
    path('payments/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]