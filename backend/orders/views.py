from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
import os
import json

from products.models import SKU, InventoryTransaction, BulkDiscount
from profiles.permissions import IsCustomer
from .models import Cart, CartItem, Reservation, Order, OrderItem, VendorOrder, Coupon
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, CouponSerializer
from notifications.utils import create_notification
from .receipts import order_receipt_json

try:
    import stripe
    STRIPE_AVAILABLE = True
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False
    STRIPE_SECRET_KEY = None
    STRIPE_PUBLISHABLE_KEY = None
    STRIPE_WEBHOOK_SECRET = None


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsCustomer]

    def list(self, request):
        cart = get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        sku_id = request.data.get("sku")
        quantity = int(request.data.get("quantity", 1))
        if not sku_id or quantity <= 0:
            return Response({"detail": "sku and positive quantity required"}, status=status.HTTP_400_BAD_REQUEST)

        sku = SKU.objects.filter(id=sku_id, product__is_active=True).first()
        if not sku:
            return Response({"detail": "SKU not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check availability
        reserved = Reservation.active_reserved_quantity(sku)
        available = max(0, sku.stock_quantity - reserved)
        if quantity > available:
            return Response({"detail": f"Only {available} units available"}, status=status.HTTP_400_BAD_REQUEST)

        cart = get_or_create_cart(request.user)
        unit_price = sku.product.price + (sku.price_adjustment or Decimal("0"))
        item, created = CartItem.objects.get_or_create(cart=cart, sku=sku, defaults={"quantity": quantity, "unit_price": unit_price})
        if not created:
            item.quantity += quantity
            item.unit_price = unit_price
            item.save()

        # Create/update reservation (15-minute hold)
        expires_at = timezone.now() + timedelta(minutes=15)
        reservation, _ = Reservation.objects.get_or_create(sku=sku, user=request.user, cart=cart, status="active", defaults={"quantity": item.quantity, "expires_at": expires_at})
        reservation.quantity = item.quantity
        reservation.expires_at = expires_at
        reservation.status = "active"
        reservation.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        item_id = request.data.get("item_id")
        quantity = int(request.data.get("quantity", 1))
        cart = get_or_create_cart(request.user)
        item = CartItem.objects.filter(id=item_id, cart=cart).first()
        if not item:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        if quantity <= 0:
            item.delete()
            Reservation.objects.filter(sku=item.sku, user=request.user, cart=cart, status="active").update(status="released")
            return Response(CartSerializer(cart).data)

        reserved = Reservation.active_reserved_quantity(item.sku) - item.quantity
        available = max(0, item.sku.stock_quantity - reserved)
        if quantity > available:
            return Response({"detail": f"Only {available} units available"}, status=status.HTTP_400_BAD_REQUEST)

        item.quantity = quantity
        item.save()
        expires_at = timezone.now() + timedelta(minutes=15)
        Reservation.objects.update_or_create(sku=item.sku, user=request.user, cart=cart, status="active", defaults={"quantity": quantity, "expires_at": expires_at})
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        item_id = request.data.get("item_id")
        cart = get_or_create_cart(request.user)
        item = CartItem.objects.filter(id=item_id, cart=cart).first()
        if not item:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        Reservation.objects.filter(sku=item.sku, user=request.user, cart=cart, status="active").update(status="released")
        item.delete()
        return Response(CartSerializer(cart).data)
    
    @action(detail=False, methods=["post"])
    def clear(self, request):
        """Clear all items from the cart"""
        cart = get_or_create_cart(request.user)
        # Release all reservations
        Reservation.objects.filter(user=request.user, cart=cart, status="active").update(status="released")
        # Delete all cart items
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)


class CheckoutView(APIView):
    permission_classes = []  # Allow unauthenticated access for guest checkout

    def post(self, request):
        # Handle guest checkout
        is_guest = request.data.get('is_guest', False)
        cart = None  # Initialize cart variable for both paths
        
        if is_guest:
            # Create a temporary cart for guest checkout
            guest_email = request.data.get('guest_email')
            guest_items = request.data.get('items', [])
            
            if not guest_email:
                return Response({"detail": "Guest email is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            if not guest_items:
                return Response({"detail": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)
                
            # Process guest items - create SimpleNamespace objects to mimic CartItem objects
            items = []
            for item_data in guest_items:
                try:
                    sku = SKU.objects.get(id=item_data.get('sku_id'))
                    quantity = int(item_data.get('quantity', 1))
                    
                    # Check stock availability
                    reserved = Reservation.active_reserved_quantity(sku)
                    available = max(0, sku.stock_quantity - reserved)
                    if quantity > available:
                        return Response({"detail": f"Insufficient stock for {sku.sku_code}"}, 
                                        status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create a SimpleNamespace object that mimics CartItem structure
                    items.append(SimpleNamespace(
                        sku=sku,
                        quantity=quantity,
                        unit_price=sku.product.price + (sku.price_adjustment or Decimal("0"))
                    ))
                except SKU.DoesNotExist:
                    return Response({"detail": f"SKU not found"}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Regular user checkout
            if not request.user.is_authenticated:
                return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
                
            cart = get_or_create_cart(request.user)
            items = list(cart.items.select_related("sku", "sku__product"))
            if not items:
                return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Get payment method from request
        payment_method = request.data.get("payment_method", "stripe")
        if payment_method not in dict(Order.PAYMENT_METHOD_CHOICES):
            return Response({"detail": "Invalid payment method"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify availability against reservations again
        for item in items:
            reserved = Reservation.active_reserved_quantity(item.sku)
            available = max(0, item.sku.stock_quantity - reserved)
            if item.quantity > available:
                return Response({"detail": f"Insufficient stock for {item.sku.sku_code}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check for coupon code
        coupon = None
        coupon_code = request.data.get("coupon_code")
        discount_amount = Decimal("0")
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid():
                    # Calculate cart total first to check coupon validity
                    cart_total = sum(item.quantity * item.unit_price for item in items)
                    if cart_total >= coupon.min_purchase_amount:
                        discount_amount = coupon.calculate_discount(cart_total)
                        # Increment coupon usage
                        coupon.current_uses += 1
                        coupon.save()
            except Coupon.DoesNotExist:
                pass  # Invalid coupon, just ignore
        
        # Create order with guest information if applicable
        order_data = {
            'status': "pending",
            'currency': "usd",
            'payment_method': payment_method,
            'coupon': coupon,
            'discount_amount': discount_amount,
            'shipping_address': request.data.get('shipping_address', {})
        }
        
        if is_guest:
            order_data.update({
                'is_guest': True,
                'guest_email': request.data.get('guest_email'),
                'guest_name': request.data.get('guest_name', ''),
                'guest_phone': request.data.get('guest_phone', '')
            })
        else:
            order_data['user'] = request.user
            
        order = Order.objects.create(**order_data)
        vendor_orders = {}
        total = Decimal("0")
        vendor_items = {}  # Track items by vendor for bulk discount calculation

        # First pass: group items by vendor
        for item in items:
            product = item.sku.product
            vendor = product.vendor
            
            if vendor.id not in vendor_items:
                vendor_items[vendor.id] = []
            vendor_items[vendor.id].append(item)

        # Second pass: process items with bulk discounts
        for item in items:
            product = item.sku.product
            vendor = product.vendor
            vo = vendor_orders.get(vendor.id)
            if not vo:
                vo = VendorOrder.objects.create(order=order, vendor=vendor, status="pending")
                vendor_orders[vendor.id] = vo
            
            # Apply bulk discount if applicable
            unit_price = item.unit_price
            vendor_quantity = sum(i.quantity for i in vendor_items[vendor.id])
            
            # Find applicable bulk discount
            bulk_discount = BulkDiscount.objects.filter(
                vendor=vendor,
                is_active=True,
                min_quantity__lte=vendor_quantity
            ).order_by('-min_quantity').first()
            
            if bulk_discount:
                discount_multiplier = Decimal(1) - (bulk_discount.discount_percentage / Decimal(100))
                unit_price = (unit_price * discount_multiplier).quantize(Decimal('0.01'))
            
            line_total = unit_price * item.quantity
            total += line_total
            OrderItem.objects.create(order=order, vendor_order=vo, sku=item.sku, product=product, 
                                    quantity=item.quantity, unit_price=unit_price)

            # Convert reservation to sale and adjust stock (only for registered users with reservations)
            if not is_guest and request.user.is_authenticated and cart:
                Reservation.objects.filter(sku=item.sku, user=request.user, cart=cart, status="active").update(status="converted")
            
            # Deduct stock for all orders
            item.sku.stock_quantity = max(0, item.sku.stock_quantity - item.quantity)
            item.sku.save()
            InventoryTransaction.objects.create(
                sku=item.sku, 
                transaction_type="sale", 
                quantity=-item.quantity, 
                reference=str(order.id), 
                notes="Checkout - Guest" if is_guest else "Checkout",
                created_by=request.user if request.user.is_authenticated else None
            )

        # Set subtotal and apply discount
        order.subtotal_amount = total
        order.total_amount = max(Decimal("0"), total - order.discount_amount)
        order.save()

        # Handle payment based on selected method
        client_secret = None
        if order.payment_method == "stripe":
            # Stripe payment processing
            if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
                try:
                    intent = stripe.PaymentIntent.create(
                        amount=int(total * 100),
                        currency=order.currency,
                        metadata={"order_id": str(order.id)},
                        description=f"Order #{order.id}"
                    )
                    order.payment_intent_id = intent.id
                    order.save(update_fields=["payment_intent_id"])
                    client_secret = intent.client_secret
                except Exception as e:
                    # Log the error but continue with order creation
                    print(f"Stripe payment intent creation failed: {str(e)}")
                    pass
        elif order.payment_method == "cod":
            # Cash on Delivery - no payment processing needed
            # Order remains in pending status until delivery and payment
            pass

        # Clear cart for registered users
        if not is_guest and request.user.is_authenticated:
            cart.items.all().delete()

        data = OrderSerializer(order).data
        if client_secret:
            data["client_secret"] = client_secret
        return Response(data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsCustomer]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        order = self.get_object()
        return order_receipt_json(order)


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can manage coupons
    
    @action(detail=False, methods=['post'], permission_classes=[IsCustomer])
    def validate(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'detail': 'Coupon code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code=code)
            if not coupon.is_valid():
                return Response({'detail': 'Coupon is not valid'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get cart total to check minimum purchase amount
            cart = get_or_create_cart(request.user)
            cart_total = sum(item.quantity * item.unit_price for item in cart.items.all())
            
            if cart_total < coupon.min_purchase_amount:
                return Response({
                    'detail': f'Minimum purchase amount of {coupon.min_purchase_amount} not met'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            discount = coupon.calculate_discount(cart_total)
            
            return Response({
                'coupon': CouponSerializer(coupon).data,
                'discount': str(discount),
                'cart_total': str(cart_total),
                'final_total': str(cart_total - discount)
            })
            
        except Coupon.DoesNotExist:
            return Response({'detail': 'Invalid coupon code'}, status=status.HTTP_404_NOT_FOUND)


class StripeConfigView(APIView):
    permission_classes = [IsCustomer]
    
    def get(self, request):
        """Return Stripe publishable key for frontend integration"""
        if not STRIPE_AVAILABLE or not STRIPE_PUBLISHABLE_KEY:
            return Response(
                {"detail": "Stripe is not configured"}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        return Response({"publishableKey": STRIPE_PUBLISHABLE_KEY})


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not STRIPE_AVAILABLE:
            return Response({"detail": "Stripe is not configured"}, status=status.HTTP_501_NOT_IMPLEMENTED)
            
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # Verify webhook signature if secret is configured
        if STRIPE_WEBHOOK_SECRET and sig_header:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, STRIPE_WEBHOOK_SECRET
                )
                # Extract data from the verified event
                event_data = event.data.object
                event_type = event.type
            except stripe.error.SignatureVerificationError:
                return Response({"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Fallback to JSON parsing if no webhook secret
            try:
                payload_data = json.loads(payload)
                event_type = payload_data.get("type")
                event_data = payload_data.get("data", {}).get("object", {})
            except json.JSONDecodeError:
                return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the event
        if event_type == "payment_intent.succeeded":
            intent_id = event_data.get("id")
            if intent_id:
                order = Order.objects.filter(payment_intent_id=intent_id).first()
                if order:
                    order.status = "paid"
                    order.save(update_fields=["status"])
                    
                    # Update vendor orders status too
                    VendorOrder.objects.filter(order=order).update(status="paid")
                    
                    # Send payment confirmation notification (only for registered users)
                    if order.user:
                        create_notification(
                            user=order.user,
                            notification_type='payment_status',
                            title='Payment Confirmed',
                            message=f'Your payment for order #{order.id} has been confirmed.',
                            reference_id=str(order.id)
                        )
                    # For guest orders, you could send email notification here instead
                    
                    return Response({"status": "payment processed", "order": str(order.id)})
        
        # Return 200 response for all webhook events to acknowledge receipt
        return Response({"received": True})