from django.urls import path
from .views import VendorProfileView, CustomerProfileView

urlpatterns = [
    path('vendor/', VendorProfileView.as_view(), name='vendor-profile'),
    path('customer/', CustomerProfileView.as_view(), name='customer-profile'),
]