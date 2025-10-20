'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useCartStore } from '@/store/cart-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ShoppingCart, Heart, Star, Package, Truck, Shield, ArrowLeft, Plus, Minus } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { toast } from 'sonner';
import { useState } from 'react';
import { ProductReviews } from '@/components/product-reviews';
import { ProductQA } from '@/components/product-qa';
import { VendorRating } from '@/components/vendor-rating';

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const addGuestItem = useCartStore((state) => state.addGuestItem);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  const { data: product, isLoading } = useQuery({
    queryKey: ['product', params.id],
    queryFn: async () => {
      const response = await apiClient.getProduct(params.id as string);
      return response.data;
    },
  });

  const addToCartMutation = useMutation({
    mutationFn: ({ sku, quantity }: { sku: string; quantity: number }) =>
      apiClient.addToCart(sku, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      toast.success('Added to cart!');
    },
    onError: () => {
      toast.error('Failed to add to cart');
    },
  });

  const addToWishlistMutation = useMutation({
    mutationFn: (sku: string) => apiClient.addToWishlist(sku),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
      toast.success('Added to wishlist!');
    },
    onError: () => {
      toast.error('Failed to add to wishlist');
    },
  });

  const handleAddToCart = () => {
    if (product.skus && product.skus.length > 0) {
      const sku = product.skus[0].sku_code;
      
      if (isAuthenticated) {
        addToCartMutation.mutate({ sku, quantity });
      } else {
        addGuestItem({
          sku,
          sku_id: product.skus[0].id,  // SKU UUID for backend API
          product_id: product.id,
          product_name: product.name,
          product_price: product.price,
          product_image: product.images?.[0]?.image,
          vendor_name: product.vendor?.business_name,
          quantity,
        });
        toast.success('Added to cart!');
        // Trigger a state update
        queryClient.invalidateQueries({ queryKey: ['guest-cart'] });
      }
    }
  };

  const handleAddToWishlist = () => {
    if (!isAuthenticated) {
      toast.error('Please login to add to wishlist');
      return;
    }
    if (product.skus && product.skus.length > 0) {
      addToWishlistMutation.mutate(product.skus[0].sku_code);
    }
  };

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse">
          <div className="grid gap-8 md:grid-cols-2">
            <div className="aspect-square rounded-lg bg-muted" />
            <div className="space-y-4">
              <div className="h-8 w-3/4 rounded bg-muted" />
              <div className="h-4 w-1/2 rounded bg-muted" />
              <div className="h-12 w-1/4 rounded bg-muted" />
              <div className="h-24 rounded bg-muted" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container flex min-h-[60vh] flex-col items-center justify-center py-10">
        <Package className="h-16 w-16 text-muted-foreground" />
        <h2 className="mt-4 text-2xl font-semibold">Product not found</h2>
        <Button className="mt-6" onClick={() => router.push('/products')}>
          Browse Products
        </Button>
      </div>
    );
  }

  const rating = product.average_rating || 4.7;
  const reviewCount = product.review_count || 128;
  const inStock = product.skus?.[0]?.stock_quantity > 0;

  return (
    <div className="container py-8">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => router.back()} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Product Images */}
        <div className="space-y-4">
          <div className="relative aspect-square overflow-hidden rounded-lg bg-muted">
            {product.images && product.images.length > 0 ? (
              <Image
                src={product.images[selectedImage]?.image || product.images[0].image}
                alt={product.name}
                fill
                className="object-cover"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <Package className="h-24 w-24 text-muted-foreground" />
              </div>
            )}
          </div>

          {/* Thumbnail Images */}
          {product.images && product.images.length > 1 && (
            <div className="grid grid-cols-4 gap-2">
              {product.images.map((image: any, index: number) => (
                <button
                  key={index}
                  onClick={() => setSelectedImage(index)}
                  className={`relative aspect-square overflow-hidden rounded-lg border-2 ${
                    selectedImage === index ? 'border-primary' : 'border-transparent'
                  }`}
                >
                  <Image
                    src={image.image}
                    alt={`${product.name} ${index + 1}`}
                    fill
                    className="object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">{product.name}</h1>
            <p className="mt-2 text-muted-foreground">
              by{' '}
              <span className="font-medium text-foreground">
                {product.vendor?.business_name || 'Vendor Store'}
              </span>
            </p>
          </div>

          {/* Rating */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <Star
                  key={i}
                  className={`h-5 w-5 ${
                    i < Math.floor(rating)
                      ? 'fill-orange-400 text-orange-400'
                      : 'text-gray-300'
                  }`}
                />
              ))}
            </div>
            <span className="text-sm font-medium">{rating.toFixed(1)}</span>
            <span className="text-sm text-muted-foreground">
              ({reviewCount} reviews)
            </span>
          </div>

          {/* Price */}
          <div className="flex items-baseline gap-3">
            <span className="text-4xl font-bold text-cyan-600 dark:text-cyan-400">
              {formatPrice(product.price)}
            </span>
            {product.compare_price && product.compare_price > product.price && (
              <>
                <span className="text-xl text-muted-foreground line-through">
                  {formatPrice(product.compare_price)}
                </span>
                <span className="rounded-full bg-orange-500 px-3 py-1 text-sm font-semibold text-white">
                  {Math.round(
                    ((product.compare_price - product.price) / product.compare_price) * 100
                  )}
                  % OFF
                </span>
              </>
            )}
          </div>

          {/* Stock Status */}
          <div>
            {inStock ? (
              <span className="text-green-600 dark:text-green-400">✓ In Stock</span>
            ) : (
              <span className="text-red-600 dark:text-red-400">✗ Out of Stock</span>
            )}
          </div>

          {/* Description */}
          <div>
            <h3 className="font-semibold">Description</h3>
            <p className="mt-2 text-muted-foreground">
              {product.description || 'No description available.'}
            </p>
          </div>

          {/* Quantity Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Quantity</label>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                disabled={quantity <= 1}
              >
                -
              </Button>
              <span className="w-12 text-center font-medium">{quantity}</span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setQuantity(quantity + 1)}
                disabled={!inStock}
              >
                +
              </Button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              size="lg"
              className="flex-1 bg-cyan-600 hover:bg-cyan-700"
              onClick={handleAddToCart}
              disabled={!inStock || addToCartMutation.isPending}
            >
              <ShoppingCart className="mr-2 h-5 w-5" />
              Add to Cart
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={handleAddToWishlist}
              disabled={addToWishlistMutation.isPending}
            >
              <Heart className="h-5 w-5" />
            </Button>
          </div>

          {/* Features */}
          <div className="space-y-3 border-t pt-6">
            <div className="flex items-center gap-3 text-sm">
              <Truck className="h-5 w-5 text-muted-foreground" />
              <span>Free shipping on orders over $50</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Shield className="h-5 w-5 text-muted-foreground" />
              <span>Secure payment & buyer protection</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Package className="h-5 w-5 text-muted-foreground" />
              <span>Easy returns within 30 days</span>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="mt-12 grid gap-6 md:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <h3 className="mb-4 font-semibold">Product Specifications</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">SKU:</dt>
                <dd className="font-medium">{product.skus?.[0]?.sku_code}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Category:</dt>
                <dd className="font-medium">{product.category?.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Stock:</dt>
                <dd className="font-medium">{product.skus?.[0]?.stock_quantity} available</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <VendorRating
          vendorId={product.vendor?.id}
          vendorName={product.vendor?.store_name || product.vendor?.business_name}
          showReviews={true}
        />
      </div>

      {/* Reviews Section */}
      <div className="mt-12">
        <ProductReviews productId={params.id as string} />
      </div>

      {/* Q&A Section */}
      <div className="mt-12">
        <ProductQA productId={params.id as string} vendorId={product?.vendor?.id} />
      </div>
    </div>
  );
}

