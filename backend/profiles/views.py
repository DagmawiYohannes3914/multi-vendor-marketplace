from django.shortcuts import render, get_object_or_404
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import VendorProfile, CustomerProfile, VendorReview
from .serializers import (
    VendorProfileSerializer, CustomerProfileSerializer, 
    VendorReviewSerializer, PublicVendorProfileSerializer
)
from .permissions import IsVendor, IsCustomer

# Create your views here.
class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get_object(self):
        return VendorProfile.objects.get(user=self.request.user)

class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    
    def get_object(self):
        return CustomerProfile.objects.get(user=self.request.user)


class PublicVendorProfileView(generics.RetrieveAPIView):
    """
    Public endpoint to retrieve vendor profile information by ID.
    Available to all users (authenticated or not).
    """
    serializer_class = PublicVendorProfileSerializer
    permission_classes = [AllowAny]
    queryset = VendorProfile.objects.all()
    lookup_field = 'pk'


class VendorReviewViewSet(viewsets.ModelViewSet):
    serializer_class = VendorReviewSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    
    def get_queryset(self):
        # Filter by vendor if vendor_id is provided in query params
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            return VendorReview.objects.filter(vendor_id=vendor_id, is_approved=True)
        # Otherwise return all reviews created by the current user
        return VendorReview.objects.filter(customer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get all reviews created by the current user"""
        reviews = VendorReview.objects.filter(customer=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def vendor_reviews(self, request):
        """Get all reviews for a specific vendor"""
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response(
                {"error": "vendor_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        reviews = VendorReview.objects.filter(vendor_id=vendor_id, is_approved=True)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
