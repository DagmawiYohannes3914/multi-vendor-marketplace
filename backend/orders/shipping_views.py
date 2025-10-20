from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import ShippingAddress, ShippingRate, OrderCancellation, ReturnRequest, Order, VendorOrder, OrderItem
from .shipping_serializers import (
    ShippingAddressSerializer, ShippingRateSerializer, 
    OrderCancellationSerializer, ReturnRequestSerializer
)
from profiles.permissions import IsVendor, IsCustomer
from notifications.utils import create_notification


class ShippingAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user shipping addresses
    
    Endpoints:
    - GET /api/orders/shipping-addresses/ - List all user addresses
    - POST /api/orders/shipping-addresses/ - Create new address
    - GET /api/orders/shipping-addresses/{id}/ - Get specific address
    - PUT /api/orders/shipping-addresses/{id}/ - Update address
    - DELETE /api/orders/shipping-addresses/{id}/ - Delete address
    - POST /api/orders/shipping-addresses/{id}/set_default/ - Set as default
    """
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return addresses for current user only"""
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set the user when creating address"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this address as default"""
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({
            'detail': 'Address set as default',
            'address': ShippingAddressSerializer(address).data
        })


class ShippingRateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing shipping rates
    
    Endpoints:
    - GET /api/orders/shipping-rates/ - List all active shipping rates
    - GET /api/orders/shipping-rates/{id}/ - Get specific rate
    - POST /api/orders/shipping-rates/calculate/ - Calculate shipping cost
    """
    serializer_class = ShippingRateSerializer
    permission_classes = [IsAuthenticated]
    queryset = ShippingRate.objects.filter(is_active=True)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate shipping cost based on weight and distance
        
        Body:
        {
            "rate_id": "uuid",
            "weight_kg": 2.5,
            "distance_km": 100
        }
        """
        rate_id = request.data.get('rate_id')
        weight = float(request.data.get('weight_kg', 1))
        distance = float(request.data.get('distance_km', 0))
        
        try:
            rate = ShippingRate.objects.get(id=rate_id, is_active=True)
            cost = rate.calculate_cost(weight, distance)
            
            return Response({
                'carrier': rate.carrier,
                'service_name': rate.service_name,
                'estimated_cost': str(cost),
                'currency': 'USD',
                'delivery_days': f"{rate.min_delivery_days}-{rate.max_delivery_days}"
            })
        except ShippingRate.DoesNotExist:
            return Response(
                {'detail': 'Shipping rate not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderCancellationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for order cancellation requests
    
    Endpoints:
    - GET /api/orders/cancellations/ - List user's cancellation requests
    - POST /api/orders/cancellations/ - Request order cancellation
    - GET /api/orders/cancellations/{id}/ - Get cancellation details
    """
    serializer_class = OrderCancellationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return cancellations for user's orders"""
        return OrderCancellation.objects.filter(order__user=self.request.user)
    
    def perform_create(self, serializer):
        """Create cancellation request"""
        order = serializer.validated_data['order']
        
        # Verify user owns the order
        if order.user != self.request.user:
            raise serializers.ValidationError("You can only cancel your own orders")
        
        # Check if order can be cancelled
        if order.status in ['delivered', 'cancelled']:
            raise serializers.ValidationError(f"Cannot cancel order with status: {order.status}")
        
        cancellation = serializer.save(
            requested_by=self.request.user,
            refund_amount=order.total_amount
        )
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        # Send notification
        create_notification(
            user=self.request.user,
            notification_type='order_status',
            title='Order Cancellation Requested',
            message=f'Your cancellation request for order #{order.id} has been submitted.',
            reference_id=str(order.id)
        )


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for return/refund requests (RMA)
    
    Customer Endpoints:
    - GET /api/orders/returns/ - List user's return requests
    - POST /api/orders/returns/ - Create return request
    - GET /api/orders/returns/{id}/ - Get return details
    
    Vendor Endpoints:
    - GET /api/orders/returns/vendor_returns/ - List vendor's return requests
    - POST /api/orders/returns/{id}/approve/ - Approve return
    - POST /api/orders/returns/{id}/reject/ - Reject return
    - POST /api/orders/returns/{id}/mark_received/ - Mark items received
    - POST /api/orders/returns/{id}/process_refund/ - Process refund
    """
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Return requests based on user role"""
        user = self.request.user
        
        # Vendors see returns for their products
        if hasattr(user, 'vendor_profile'):
            return ReturnRequest.objects.filter(vendor_order__vendor=user.vendor_profile)
        
        # Customers see their own returns
        return ReturnRequest.objects.filter(order__user=user)
    
    def perform_create(self, serializer):
        """Create return request"""
        order = serializer.validated_data['order']
        vendor_order = serializer.validated_data['vendor_order']
        
        # Verify user owns the order
        if order.user != self.request.user:
            raise serializers.ValidationError("You can only request returns for your own orders")
        
        # Verify order is eligible for return (within 30 days, delivered)
        if order.status not in ['delivered', 'paid']:
            raise serializers.ValidationError("Order must be delivered to request return")
        
        return_request = serializer.save()
        
        # Send notification to vendor
        if hasattr(vendor_order.vendor.user, 'email'):
            create_notification(
                user=vendor_order.vendor.user,
                notification_type='order_status',
                title='New Return Request',
                message=f'Return request {return_request.rma_number} received',
                reference_id=str(return_request.id)
            )
        
        # Send notification to customer
        create_notification(
            user=self.request.user,
            notification_type='order_status',
            title='Return Request Submitted',
            message=f'Your return request {return_request.rma_number} has been submitted',
            reference_id=str(return_request.id)
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsVendor])
    def vendor_returns(self, request):
        """Get all return requests for vendor's products"""
        vendor_profile = request.user.vendor_profile
        returns = ReturnRequest.objects.filter(vendor_order__vendor=vendor_profile)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            returns = returns.filter(status=status_filter)
        
        serializer = self.get_serializer(returns, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsVendor])
    def approve(self, request, pk=None):
        """Approve return request (vendor only)"""
        return_request = self.get_object()
        
        # Verify vendor owns this return
        if return_request.vendor_order.vendor != request.user.vendor_profile:
            return Response(
                {'detail': 'You can only approve returns for your products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if return_request.status != 'pending':
            return Response(
                {'detail': 'Can only approve pending returns'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return_request.status = 'approved'
        return_request.approved_at = timezone.now()
        return_request.vendor_notes = request.data.get('notes', '')
        return_request.save()
        
        # Notify customer
        create_notification(
            user=return_request.order.user,
            notification_type='order_status',
            title='Return Request Approved',
            message=f'Your return request {return_request.rma_number} has been approved',
            reference_id=str(return_request.id)
        )
        
        return Response({
            'detail': 'Return request approved',
            'return': ReturnRequestSerializer(return_request).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsVendor])
    def reject(self, request, pk=None):
        """Reject return request (vendor only)"""
        return_request = self.get_object()
        
        if return_request.vendor_order.vendor != request.user.vendor_profile:
            return Response(
                {'detail': 'You can only reject returns for your products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if return_request.status != 'pending':
            return Response(
                {'detail': 'Can only reject pending returns'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return_request.status = 'rejected'
        return_request.vendor_notes = request.data.get('notes', '')
        return_request.save()
        
        # Notify customer
        create_notification(
            user=return_request.order.user,
            notification_type='order_status',
            title='Return Request Rejected',
            message=f'Your return request {return_request.rma_number} has been rejected. Reason: {return_request.vendor_notes}',
            reference_id=str(return_request.id)
        )
        
        return Response({
            'detail': 'Return request rejected',
            'return': ReturnRequestSerializer(return_request).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsVendor])
    def mark_received(self, request, pk=None):
        """Mark return items as received (vendor only)"""
        return_request = self.get_object()
        
        if return_request.vendor_order.vendor != request.user.vendor_profile:
            return Response(
                {'detail': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if return_request.status != 'approved':
            return Response(
                {'detail': 'Can only mark approved returns as received'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return_request.status = 'received'
        return_request.received_at = timezone.now()
        return_request.save()
        
        # Notify customer
        create_notification(
            user=return_request.order.user,
            notification_type='order_status',
            title='Return Items Received',
            message=f'Your return items for {return_request.rma_number} have been received',
            reference_id=str(return_request.id)
        )
        
        return Response({
            'detail': 'Return marked as received',
            'return': ReturnRequestSerializer(return_request).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsVendor])
    def process_refund(self, request, pk=None):
        """Process refund for return (vendor only)"""
        return_request = self.get_object()
        
        if return_request.vendor_order.vendor != request.user.vendor_profile:
            return Response(
                {'detail': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if return_request.status != 'received':
            return Response(
                {'detail': 'Can only refund received returns'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate refund amount (can include restocking fee)
        refund_amount = request.data.get('refund_amount')
        restocking_fee = request.data.get('restocking_fee', 0)
        
        return_request.refund_amount = refund_amount
        return_request.restocking_fee = restocking_fee
        return_request.status = 'refunded'
        return_request.refunded_at = timezone.now()
        return_request.refund_transaction_id = f"REFUND-{return_request.rma_number}"
        return_request.save()
        
        # TODO: Integrate with actual payment processor to issue refund
        
        # Notify customer
        create_notification(
            user=return_request.order.user,
            notification_type='payment_status',
            title='Refund Processed',
            message=f'Refund of ${refund_amount} has been processed for {return_request.rma_number}',
            reference_id=str(return_request.id)
        )
        
        return Response({
            'detail': 'Refund processed successfully',
            'refund_amount': str(refund_amount),
            'restocking_fee': str(restocking_fee),
            'return': ReturnRequestSerializer(return_request).data
        })

