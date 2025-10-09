from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import VendorProfile, CustomerProfile
from .serializers import VendorProfileSerializer, CustomerProfileSerializer

# Create your views here.
class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return VendorProfile.objects.get(user=self.request.user)

class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return CustomerProfile.objects.get(user=self.request.user)
