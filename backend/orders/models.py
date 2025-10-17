from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from decimal import Decimal

from products.models import SKU, Product, InventoryTransaction
from profiles.models import VendorProfile

User = get_user_model()


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=0)  # 0 means unlimited
    current_uses = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{' %' if self.discount_type == 'percentage' else ''}"
    
    def calculate_discount(self, total_amount):
        if not self.is_valid():
            return Decimal('0.00')
        
        if total_amount < self.min_purchase_amount:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            return (total_amount * self.discount_value / 100).quantize(Decimal('0.01'))
        else:
            return min(self.discount_value, total_amount)
    
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        return True


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user.username})"


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "sku")

    def __str__(self):
        return f"{self.sku.sku_code} x{self.quantity}"


class Reservation(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("converted", "Converted"),
        ("released", "Released"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name="reservations")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="reservations")
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservation({self.sku.sku_code}, {self.quantity})"

    @staticmethod
    def active_reserved_quantity(sku):
        now = timezone.now()
        return (
            Reservation.objects.filter(sku=sku, status="active", expires_at__gt=now)
            .aggregate(models.Sum("quantity"))["quantity__sum"]
            or 0
        )


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )
    PAYMENT_METHOD_CHOICES = (
        ("stripe", "Stripe"),
        ("cod", "Cash on Delivery"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders", null=True, blank=True)
    guest_email = models.EmailField(blank=True, null=True)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    is_guest = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="stripe")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=10, default="usd")
    payment_intent_id = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.is_guest:
            return f"Order({self.id}, Guest: {self.guest_email}, {self.status})"
        return f"Order({self.id}, {self.user.username if self.user else 'Unknown'}, {self.status})"


class VendorOrder(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="vendor_orders")
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"VendorOrder({self.vendor.store_name}, {self.order.id})"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.CASCADE, related_name="items")
    sku = models.ForeignKey(SKU, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"OrderItem({self.product}, x{self.quantity})"


class ShippingAddress(models.Model):
    """
    Model for storing multiple shipping addresses per user
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    label = models.CharField(max_length=50, help_text="e.g., Home, Office, etc.")
    recipient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = 'Shipping Addresses'
    
    def __str__(self):
        return f"{self.label} - {self.recipient_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class ShippingRate(models.Model):
    """
    Model for shipping rate calculation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.CharField(max_length=100)
    service_name = models.CharField(max_length=100)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_delivery_days = models.PositiveIntegerField(default=3)
    max_delivery_days = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.carrier} - {self.service_name}"
    
    def calculate_cost(self, weight_kg=1, distance_km=0):
        """Calculate shipping cost based on weight and distance"""
        cost = self.base_cost + (weight_kg * self.cost_per_kg) + (distance_km * self.cost_per_km)
        return cost.quantize(Decimal('0.01'))


class OrderCancellation(models.Model):
    """
    Model for order cancellation requests
    """
    REASON_CHOICES = (
        ('customer_request', 'Customer Request'),
        ('out_of_stock', 'Out of Stock'),
        ('payment_failed', 'Payment Failed'),
        ('fraud', 'Suspected Fraud'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='cancellation')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_cancellations')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_processed = models.BooleanField(default=False)
    refund_transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Cancellation for Order {self.order.id}"


class ReturnRequest(models.Model):
    """
    Model for product return requests (RMA)
    """
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('received', 'Item Received'),
        ('refunded', 'Refunded'),
        ('completed', 'Completed'),
    )
    
    REASON_CHOICES = (
        ('defective', 'Defective/Damaged'),
        ('wrong_item', 'Wrong Item Sent'),
        ('not_as_described', 'Not As Described'),
        ('changed_mind', 'Changed Mind'),
        ('size_issue', 'Size/Fit Issue'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rma_number = models.CharField(max_length=20, unique=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.CASCADE, related_name='returns')
    items = models.ManyToManyField(OrderItem, related_name='return_requests')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    images = models.JSONField(default=list, blank=True, help_text="List of image URLs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    restocking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_method = models.CharField(max_length=50, default='original_payment')
    refund_transaction_id = models.CharField(max_length=100, blank=True)
    vendor_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"RMA #{self.rma_number} - Order {self.order.id}"
    
    def save(self, *args, **kwargs):
        if not self.rma_number:
            # Generate RMA number
            import random
            import string
            self.rma_number = 'RMA' + ''.join(random.choices(string.digits, k=10))
        super().save(*args, **kwargs)