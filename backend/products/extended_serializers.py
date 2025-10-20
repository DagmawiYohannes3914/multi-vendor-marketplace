from rest_framework import serializers
from django.db.models import Avg, Sum
from .models import (
    ReviewImage, ReviewVote, ProductQuestion, ProductAnswer, RecentlyViewed,
    ProductComparison, FlashSale, BundleDeal, LoyaltyPoints, ReferralProgram,
    ProductBadge, StockAlert, Product, ProductRating
)


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'review', 'image', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class ReviewVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVote
        fields = ['id', 'review', 'user', 'vote_type', 'created_at']
        read_only_fields = ['user', 'created_at']


class ProductRatingWithVotesSerializer(serializers.ModelSerializer):
    helpful_votes = serializers.SerializerMethodField()
    not_helpful_votes = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    images = ReviewImageSerializer(many=True, read_only=True)
    is_verified_purchase = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductRating
        fields = ['id', 'product', 'user', 'rating', 'review', 'images',
                 'helpful_votes', 'not_helpful_votes', 'user_vote', 
                 'is_verified_purchase', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_helpful_votes(self, obj):
        return obj.votes.filter(vote_type='helpful').count()
    
    def get_not_helpful_votes(self, obj):
        return obj.votes.filter(vote_type='not_helpful').count()
    
    def get_user_vote(self, obj):
        user = self.context.get('request').user if 'request' in self.context else None
        if user and user.is_authenticated:
            vote = obj.votes.filter(user=user).first()
            return vote.vote_type if vote else None
        return None
    
    def get_is_verified_purchase(self, obj):
        # Check if user purchased this product
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            order__user=obj.user,
            product=obj.product,
            order__status__in=['paid', 'delivered']
        ).exists()


class ProductQuestionSerializer(serializers.ModelSerializer):
    answers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductQuestion
        fields = ['id', 'product', 'user', 'question', 'is_answered', 
                 'answers_count', 'created_at']
        read_only_fields = ['user', 'is_answered', 'created_at']
    
    def get_answers_count(self, obj):
        return obj.answers.count()


class ProductAnswerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProductAnswer
        fields = ['id', 'question', 'user', 'username', 'answer', 'is_vendor', 
                 'helpful_votes', 'created_at']
        read_only_fields = ['user', 'is_vendor', 'helpful_votes', 'created_at']


class RecentlyViewedSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, 
                                            decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = RecentlyViewed
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 
                 'viewed_at']
        read_only_fields = ['viewed_at']
    
    def get_product_image(self, obj):
        primary_image = obj.product.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url if hasattr(primary_image.image, 'url') else None
        return None


class ProductComparisonSerializer(serializers.ModelSerializer):
    products_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductComparison
        fields = ['id', 'user', 'products', 'products_details', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_products_details(self, obj):
        products_data = []
        for product in obj.products.all():
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'price': str(product.price),
                'rating': str(product.ratings.aggregate(avg=serializers.Avg('rating'))['avg'] or 0),
                'category': product.category.name if product.category else None
            })
        return products_data


class FlashSaleSerializer(serializers.ModelSerializer):
    is_live_now = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FlashSale
        fields = ['id', 'name', 'description', 'discount_percentage', 'start_time', 
                 'end_time', 'products', 'products_count', 'max_quantity_per_user', 
                 'is_active', 'is_live_now', 'created_at']
        read_only_fields = ['created_at']
    
    def get_is_live_now(self, obj):
        return obj.is_live()
    
    def get_products_count(self, obj):
        return obj.products.count()


class BundleDealSerializer(serializers.ModelSerializer):
    total_regular_price = serializers.SerializerMethodField()
    savings = serializers.SerializerMethodField()
    
    class Meta:
        model = BundleDeal
        fields = ['id', 'name', 'description', 'bundle_products', 'bundle_price', 
                 'discount_percentage', 'total_regular_price', 'savings', 
                 'is_active', 'valid_from', 'valid_to', 'created_at']
        read_only_fields = ['created_at']
    
    def get_total_regular_price(self, obj):
        from django.db.models import Sum
        total = obj.bundle_products.aggregate(Sum('price'))['price__sum'] or 0
        return str(total)
    
    def get_savings(self, obj):
        from decimal import Decimal
        total = obj.bundle_products.aggregate(Sum('price'))['price__sum'] or Decimal('0')
        return str(total - obj.bundle_price)


class LoyaltyPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyPoints
        fields = ['id', 'user', 'points', 'transaction_type', 'reference', 
                 'description', 'created_at']
        read_only_fields = ['user', 'created_at']


class ReferralProgramSerializer(serializers.ModelSerializer):
    referrer_name = serializers.CharField(source='referrer.username', read_only=True)
    referred_name = serializers.CharField(source='referred.username', read_only=True, 
                                         allow_null=True)
    
    class Meta:
        model = ReferralProgram
        fields = ['id', 'referrer', 'referrer_name', 'referred', 'referred_name', 
                 'referral_code', 'email', 'reward_points', 'status', 
                 'created_at', 'completed_at']
        read_only_fields = ['referrer', 'referral_code', 'status', 'created_at', 
                           'completed_at']


class ProductBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBadge
        fields = ['id', 'product', 'badge_type', 'expires_at', 'created_at']
        read_only_fields = ['created_at']


class StockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='sku.product.name', read_only=True)
    sku_code = serializers.CharField(source='sku.sku_code', read_only=True)
    
    class Meta:
        model = StockAlert
        fields = ['id', 'user', 'sku', 'product_name', 'sku_code', 'email_sent', 
                 'notified_at', 'created_at']
        read_only_fields = ['user', 'email_sent', 'notified_at', 'created_at']

