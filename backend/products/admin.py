from django.contrib import admin
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import Category, Product, ProductImage, SKU, InventoryTransaction, ProductRating

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'name', 'slug', 'is_active')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    list_filter = ('is_active',)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class SKUInline(admin.TabularInline):
    model = SKU
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'category', 'price', 'is_featured', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_featured', 'vendor', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, SKUInline]
    date_hierarchy = 'created_at'

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'product', 'price_adjustment', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('sku_code', 'product__name')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('sku', 'transaction_type', 'quantity', 'reference', 'created_at', 'created_by')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('sku__sku_code', 'reference', 'notes')
    date_hierarchy = 'created_at'

@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'review')
    date_hierarchy = 'created_at'
