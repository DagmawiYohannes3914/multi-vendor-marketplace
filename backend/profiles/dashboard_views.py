from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F, DecimalField, ExpressionWrapper
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from orders.models import VendorOrder, OrderItem
from products.models import Product, SKU
from .models import VendorProfile
from .permissions import IsVendor
from .dashboard_serializers import (
    VendorDashboardStatsSerializer,
    VendorOrderListSerializer,
    VendorOrderDetailSerializer,
    VendorOrderUpdateSerializer,
    ProductPerformanceSerializer,
    LowStockAlertSerializer,
    RevenueReportSerializer,
    VendorOrderItemSerializer
)
from notifications.utils import create_notification


class VendorDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for vendor dashboard operations
    """
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get_vendor_profile(self, request):
        """Helper method to get vendor profile"""
        if not hasattr(request.user, 'vendor_profile'):
            return None
        return request.user.vendor_profile
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get overall dashboard statistics for vendor
        GET /api/profiles/vendor/dashboard/stats/
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate date ranges
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
        end_of_last_month = start_of_month - timedelta(seconds=1)
        
        # Get all vendor orders
        all_orders = VendorOrder.objects.filter(vendor=vendor)
        
        # Total revenue (all paid orders)
        total_revenue = all_orders.filter(
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Total orders
        total_orders = all_orders.count()
        
        # Pending orders
        pending_orders = all_orders.filter(status='pending').count()
        
        # Product stats
        all_products = Product.objects.filter(vendor=vendor)
        total_products = all_products.count()
        active_products = all_products.filter(is_active=True).count()
        
        # Low stock products (less than 10 items)
        low_stock_products = SKU.objects.filter(
            product__vendor=vendor,
            stock_quantity__lt=10,
            is_active=True
        ).count()
        
        # This month's stats
        this_month_orders = all_orders.filter(order__created_at__gte=start_of_month)
        revenue_this_month = this_month_orders.filter(
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        orders_this_month = this_month_orders.count()
        
        # Last month's stats
        last_month_orders = all_orders.filter(
            order__created_at__gte=start_of_last_month,
            order__created_at__lte=end_of_last_month
        )
        revenue_last_month = last_month_orders.filter(
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        orders_last_month = last_month_orders.count()
        
        stats_data = {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_products': total_products,
            'active_products': active_products,
            'low_stock_products': low_stock_products,
            'average_rating': vendor.average_rating,
            'total_reviews': vendor.total_reviews,
            'revenue_this_month': revenue_this_month,
            'revenue_last_month': revenue_last_month,
            'orders_this_month': orders_this_month,
            'orders_last_month': orders_last_month,
        }
        
        serializer = VendorDashboardStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def orders(self, request):
        """
        Get list of vendor orders with filtering
        GET /api/profiles/vendor/dashboard/orders/?status=pending&search=customer_name
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all vendor orders
        queryset = VendorOrder.objects.filter(vendor=vendor).select_related(
            'order', 'order__user'
        ).prefetch_related('items').order_by('-order__created_at')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search by customer name/email
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(order__user__first_name__icontains=search) |
                Q(order__user__last_name__icontains=search) |
                Q(order__user__email__icontains=search) |
                Q(order__guest_name__icontains=search) |
                Q(order__guest_email__icontains=search)
            )
        
        # Date range filter
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(order__created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(order__created_at__lte=end_date)
        
        # Annotate with items count
        queryset = queryset.annotate(items_count=Count('items'))
        
        # Build response data
        orders_data = []
        for vendor_order in queryset:
            orders_data.append({
                'id': vendor_order.id,
                'order': vendor_order.order,
                'status': vendor_order.status,
                'total_amount': vendor_order.total_amount,
                'tracking_number': vendor_order.tracking_number,
                'estimated_delivery': vendor_order.estimated_delivery,
                'items_count': vendor_order.items_count,
            })
        
        serializer = VendorOrderListSerializer(orders_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def order_detail(self, request):
        """
        Get detailed view of a specific vendor order
        GET /api/profiles/vendor/dashboard/order_detail/?order_id=xxx
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({"detail": "order_id parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vendor_order = VendorOrder.objects.select_related(
                'order', 'order__user', 'vendor'
            ).prefetch_related('items__product', 'items__sku').get(
                id=order_id,
                vendor=vendor
            )
        except VendorOrder.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Build items data
        items_data = []
        for item in vendor_order.items.all():
            items_data.append({
                'product_name': item.product.name if item.product else 'Unknown',
                'sku_code': item.sku.sku_code if item.sku else 'N/A',
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total': item.quantity * item.unit_price
            })
        
        order_data = {
            'id': vendor_order.id,
            'order': vendor_order.order,
            'status': vendor_order.status,
            'total_amount': vendor_order.total_amount,
            'tracking_number': vendor_order.tracking_number,
            'carrier': vendor_order.carrier,
            'estimated_delivery': vendor_order.estimated_delivery,
            'shipped_at': vendor_order.shipped_at,
            'delivered_at': vendor_order.delivered_at,
            'items': items_data
        }
        
        serializer = VendorOrderDetailSerializer(order_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_order(self, request):
        """
        Update vendor order status
        POST /api/profiles/vendor/dashboard/update_order/
        Body: {
            "order_id": "xxx",
            "status": "shipped",
            "tracking_number": "TRACK123",
            "carrier": "UPS"
        }
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"detail": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vendor_order = VendorOrder.objects.select_related('order', 'order__user').get(
                id=order_id,
                vendor=vendor
            )
        except VendorOrder.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = VendorOrderUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order
        old_status = vendor_order.status
        vendor_order.status = serializer.validated_data['status']
        
        if 'tracking_number' in serializer.validated_data:
            vendor_order.tracking_number = serializer.validated_data['tracking_number']
        
        if 'carrier' in serializer.validated_data:
            vendor_order.carrier = serializer.validated_data['carrier']
        
        if 'estimated_delivery' in serializer.validated_data:
            vendor_order.estimated_delivery = serializer.validated_data['estimated_delivery']
        
        # Update timestamps
        if vendor_order.status == 'shipped' and old_status != 'shipped':
            vendor_order.shipped_at = timezone.now()
        
        if vendor_order.status == 'delivered' and old_status != 'delivered':
            vendor_order.delivered_at = timezone.now()
        
        vendor_order.save()
        
        # Send notification to customer (only for registered users)
        if vendor_order.order.user:
            notification_messages = {
                'processing': 'Your order is being processed',
                'shipped': f'Your order has been shipped. Tracking: {vendor_order.tracking_number}',
                'delivered': 'Your order has been delivered',
                'cancelled': 'Your order has been cancelled'
            }
            
            if vendor_order.status in notification_messages:
                create_notification(
                    user=vendor_order.order.user,
                    notification_type='order_status',
                    title='Order Status Update',
                    message=notification_messages[vendor_order.status],
                    reference_id=str(vendor_order.order.id)
                )
        
        return Response({
            "detail": "Order updated successfully",
            "status": vendor_order.status
        })
    
    @action(detail=False, methods=['get'])
    def product_performance(self, request):
        """
        Get product performance metrics
        GET /api/profiles/vendor/dashboard/product_performance/?limit=10
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        limit = int(request.query_params.get('limit', 10))
        
        # Get product performance data
        products = Product.objects.filter(vendor=vendor).annotate(
            total_sold=Sum('orderitem__quantity', filter=Q(
                orderitem__vendor_order__status__in=['paid', 'processing', 'shipped', 'delivered']
            )),
            total_revenue=Sum(
                ExpressionWrapper(
                    F('orderitem__quantity') * F('orderitem__unit_price'),
                    output_field=DecimalField()
                ),
                filter=Q(orderitem__vendor_order__status__in=['paid', 'processing', 'shipped', 'delivered'])
            ),
            average_rating=Avg('ratings__rating'),
            total_reviews=Count('ratings')
        ).order_by('-total_sold')[:limit]
        
        # Build response data
        performance_data = []
        for product in products:
            # Get current stock from all SKUs
            current_stock = SKU.objects.filter(product=product).aggregate(
                total=Sum('stock_quantity')
            )['total'] or 0
            
            performance_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'total_sold': product.total_sold or 0,
                'total_revenue': product.total_revenue or Decimal('0.00'),
                'current_stock': current_stock,
                'average_rating': product.average_rating or Decimal('0.00'),
                'total_reviews': product.total_reviews or 0
            })
        
        serializer = ProductPerformanceSerializer(performance_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """
        Get low stock alerts for vendor products
        GET /api/profiles/vendor/dashboard/low_stock_alerts/?threshold=10
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        threshold = int(request.query_params.get('threshold', 10))
        
        # Get low stock SKUs
        low_stock_skus = SKU.objects.filter(
            product__vendor=vendor,
            stock_quantity__lt=threshold,
            is_active=True
        ).select_related('product').order_by('stock_quantity')
        
        alerts_data = []
        for sku in low_stock_skus:
            status_label = 'critical' if sku.stock_quantity == 0 else 'low' if sku.stock_quantity < 5 else 'warning'
            alerts_data.append({
                'product_id': sku.product.id,
                'product_name': sku.product.name,
                'sku_code': sku.sku_code,
                'sku_id': sku.id,
                'current_stock': sku.stock_quantity,
                'status': status_label
            })
        
        serializer = LowStockAlertSerializer(alerts_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def revenue_report(self, request):
        """
        Get revenue report by period
        GET /api/profiles/vendor/dashboard/revenue_report/?period=daily&days=30
        GET /api/profiles/vendor/dashboard/revenue_report/?period=monthly&months=12
        """
        vendor = self.get_vendor_profile(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        period = request.query_params.get('period', 'daily')
        
        if period == 'daily':
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Get daily revenue
            orders = VendorOrder.objects.filter(
                vendor=vendor,
                order__created_at__gte=start_date,
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).extra(select={'date': 'DATE(orders_order.created_at)'}).values('date').annotate(
                revenue=Sum('total_amount'),
                orders_count=Count('id'),
                items_sold=Sum('items__quantity')
            ).order_by('date')
            
            report_data = [{
                'period': item['date'].strftime('%Y-%m-%d') if hasattr(item['date'], 'strftime') else str(item['date']),
                'revenue': item['revenue'],
                'orders_count': item['orders_count'],
                'items_sold': item['items_sold'] or 0
            } for item in orders]
            
        elif period == 'monthly':
            months = int(request.query_params.get('months', 12))
            start_date = timezone.now() - timedelta(days=months * 30)
            
            # Get monthly revenue
            orders = VendorOrder.objects.filter(
                vendor=vendor,
                order__created_at__gte=start_date,
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).extra(
                select={'month': "TO_CHAR(orders_order.created_at, 'YYYY-MM')"}
            ).values('month').annotate(
                revenue=Sum('total_amount'),
                orders_count=Count('id'),
                items_sold=Sum('items__quantity')
            ).order_by('month')
            
            report_data = [{
                'period': item['month'],
                'revenue': item['revenue'],
                'orders_count': item['orders_count'],
                'items_sold': item['items_sold'] or 0
            } for item in orders]
        else:
            return Response({"detail": "Invalid period. Use 'daily' or 'monthly'"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RevenueReportSerializer(report_data, many=True)
        return Response(serializer.data)

