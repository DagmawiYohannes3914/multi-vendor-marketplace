from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from decimal import Decimal
import os
import json

from products.models import SKU, InventoryTransaction
from profiles.permissions import IsCustomer
from .models import Cart, CartItem, Reservation, Order, OrderItem, VendorOrder
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer

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


class CheckoutView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
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

        order = Order.objects.create(
            user=request.user, 
            status="pending", 
            currency="usd",
            payment_method=payment_method
        )
        vendor_orders = {}
        total = Decimal("0")

        for item in items:
            product = item.sku.product
            vendor = product.vendor
            vo = vendor_orders.get(vendor.id)
            if not vo:
                vo = VendorOrder.objects.create(order=order, vendor=vendor, status="pending")
                vendor_orders[vendor.id] = vo
            line_total = item.unit_price * item.quantity
            total += line_total
            OrderItem.objects.create(order=order, vendor_order=vo, sku=item.sku, product=product, quantity=item.quantity, unit_price=item.unit_price)

            # Convert reservation to sale and adjust stock
            Reservation.objects.filter(sku=item.sku, user=request.user, cart=cart, status="active").update(status="converted")
            item.sku.stock_quantity = max(0, item.sku.stock_quantity - item.quantity)
            item.sku.save()
            InventoryTransaction.objects.create(sku=item.sku, transaction_type="sale", quantity=-item.quantity, reference=str(order.id), notes="Checkout")

        order.total_amount = total
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

        # Clear cart
        cart.items.all().delete()

        data = OrderSerializer(order).data
        if client_secret:
            data["client_secret"] = client_secret
        return Response(data, status=status.HTTP_201_CREATED)


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
                    
                    return Response({"status": "payment processed", "order": str(order.id)})
        
        # Return 200 response for all webhook events to acknowledge receipt
        return Response({"received": True})