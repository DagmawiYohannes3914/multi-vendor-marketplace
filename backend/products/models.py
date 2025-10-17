from django.db import models
from django.contrib.auth import get_user_model
from mptt.models import MPTTModel, TreeForeignKey
from profiles.models import VendorProfile
import uuid

User = get_user_model()

class Category(MPTTModel):
    """
    Hierarchical category model using MPTT for efficient tree operations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Product model with vendor relationship
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class ProductImage(models.Model):
    """
    Product images model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product.name}"

class SKU(models.Model):
    """
    Stock Keeping Unit model for product variants
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='skus')
    sku_code = models.CharField(max_length=50, unique=True)
    attributes = models.JSONField(default=dict, blank=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.sku_code

class InventoryTransaction(models.Model):
    """
    Inventory transaction model for tracking stock changes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TRANSACTION_TYPES = (
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
    )
    
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()  # Can be negative for sales/adjustments
    reference = models.CharField(max_length=100, blank=True)  # Order number, etc.
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.sku.sku_code} - {self.quantity}"

class ProductRating(models.Model):
    """
    Product rating model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'user')  # One rating per user per product
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"


class Wishlist(models.Model):
    """
    Wishlist model for users to save products they're interested in
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    products = models.ManyToManyField(Product, related_name='in_wishlists')
    name = models.CharField(max_length=100, default="My Wishlist")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class BulkDiscount(models.Model):
    """
    Bulk discount model for automatic discounts when customers purchase multiple items from the same vendor
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('profiles.VendorProfile', on_delete=models.CASCADE, related_name='bulk_discounts')
    min_quantity = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_quantity']
        unique_together = ('vendor', 'min_quantity')
    
    def __str__(self):
        return f"{self.vendor.store_name} - {self.min_quantity}+ items: {self.discount_percentage}% off"


class ProductComment(models.Model):
    """
    Model for product comments, allowing both registered users and guests to comment
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='product_comments')
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"Comment by {self.user.username} on {self.product.name}"
        return f"Comment by {self.guest_name or 'Anonymous'} on {self.product.name}"


class ReviewImage(models.Model):
    """
    Model for product review images
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(ProductRating, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for review by {self.review.user.username}"


class ReviewVote(models.Model):
    """
    Model for helpful review voting
    """
    VOTE_CHOICES = (
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(ProductRating, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=15, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.vote_type} on review"


class ProductQuestion(models.Model):
    """
    Model for product Q&A
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    question = models.TextField()
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Question by {self.user.username} on {self.product.name}"


class ProductAnswer(models.Model):
    """
    Model for product Q&A answers
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    answer = models.TextField()
    is_vendor = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-helpful_votes', '-created_at']
    
    def __str__(self):
        return f"Answer by {self.user.username}"


class RecentlyViewed(models.Model):
    """
    Model for tracking recently viewed products
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-viewed_at']
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"


class ProductComparison(models.Model):
    """
    Model for product comparison lists
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='comparisons')
    products = models.ManyToManyField(Product, related_name='in_comparisons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comparison by {self.user.username}"


class FlashSale(models.Model):
    """
    Model for time-limited flash sales
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    products = models.ManyToManyField(Product, related_name='flash_sales')
    max_quantity_per_user = models.PositiveIntegerField(default=0)  # 0 means no limit
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def is_live(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time


class BundleDeal(models.Model):
    """
    Model for bundle deals (Buy X get Y)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    bundle_products = models.ManyToManyField(Product, related_name='bundle_deals')
    bundle_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class LoyaltyPoints(models.Model):
    """
    Model for loyalty points system
    """
    TRANSACTION_TYPES = (
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('adjusted', 'Manual Adjustment'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='loyalty_points')
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=100, blank=True)  # Order ID, etc.
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points"
    
    @staticmethod
    def get_user_balance(user):
        """Get total loyalty points balance for a user"""
        from django.db.models import Sum
        total = LoyaltyPoints.objects.filter(user=user).aggregate(Sum('points'))['points__sum']
        return total or 0


class ReferralProgram(models.Model):
    """
    Model for referral program
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='referrals_made')
    referred = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='referred_by', null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    reward_points = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Referral by {self.referrer.username} - {self.referral_code}"


class ProductBadge(models.Model):
    """
    Model for product badges (New, Sale, Best Seller, etc.)
    """
    BADGE_TYPES = (
        ('new', 'New Arrival'),
        ('sale', 'On Sale'),
        ('bestseller', 'Best Seller'),
        ('trending', 'Trending'),
        ('limited', 'Limited Edition'),
        ('featured', 'Featured'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'badge_type')
    
    def __str__(self):
        return f"{self.product.name} - {self.badge_type}"


class StockAlert(models.Model):
    """
    Model for stock availability notifications
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE)
    email_sent = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'sku')
    
    def __str__(self):
        return f"Stock alert for {self.user.username} - {self.sku.sku_code}"