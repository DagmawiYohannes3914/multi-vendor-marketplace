from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CheckoutView, StripeWebhookView, StripeConfigView

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payments/stripe/config/', StripeConfigView.as_view(), name='stripe-config'),
    path('payments/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]