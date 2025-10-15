from rest_framework import serializers
from .models import Category, Product, ProductImage, SKU, InventoryTransaction, ProductRating

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'image', 'is_active']

class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'children']
    
    def get_children(self, obj):
        return CategoryTreeSerializer(obj.get_children(), many=True).data

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary']

class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ['id', 'sku_code', 'attributes', 'price_adjustment', 'stock_quantity', 'is_active']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    skus = SKUSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'compare_price',
            'is_featured', 'is_active', 'created_at', 'updated_at',
            'vendor', 'vendor_name', 'category', 'category_name',
            'images', 'skus', 'average_rating'
        ]
    
    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / len(ratings)

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'price', 'compare_price',
            'is_featured', 'is_active'
        ]
    
    def create(self, validated_data):
        # Set the vendor based on the authenticated user's vendor profile
        user = self.context['request'].user
        validated_data['vendor'] = user.vendorprofile
        
        # Generate a slug from the name
        from django.utils.text import slugify
        validated_data['slug'] = slugify(validated_data['name'])
        
        return super().create(validated_data)

class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = ['id', 'sku', 'transaction_type', 'quantity', 'reference', 'notes', 'created_at']
    
    def create(self, validated_data):
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class ProductRatingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProductRating
        fields = ['id', 'product', 'rating', 'review', 'created_at', 'user', 'username']
        read_only_fields = ['user']
    
    def create(self, validated_data):
        # Set the user field to the current user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)