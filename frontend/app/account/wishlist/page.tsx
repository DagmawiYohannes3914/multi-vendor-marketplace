'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useCartStore } from '@/store/cart-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Heart, ShoppingCart, Trash2, ArrowLeft } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { toast } from 'sonner';

export default function WishlistPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const addGuestItem = useCartStore((state) => state.addGuestItem);

  const { data: wishlists, isLoading } = useQuery({
    queryKey: ['wishlist'],
    queryFn: async () => {
      const response = await apiClient.getWishlist();
      return response.data;
    },
    enabled: isAuthenticated,
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

  const removeFromWishlistMutation = useMutation({
    mutationFn: ({ wishlistId, productId }: { wishlistId: string; productId: string }) =>
      apiClient.removeFromWishlist(wishlistId, productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
      toast.success('Removed from wishlist');
    },
    onError: () => {
      toast.error('Failed to remove from wishlist');
    },
  });

  if (!isAuthenticated) {
    router.push('/auth/login');
    return null;
  }

  const handleAddToCart = (product: any) => {
    if (product.skus && product.skus.length > 0) {
      const sku = product.skus[0].sku_code;
      if (isAuthenticated) {
        addToCartMutation.mutate({ sku, quantity: 1 });
      } else {
        addGuestItem({
          sku,
          sku_id: product.skus[0].id,
          product_id: product.id,
          product_name: product.name,
          product_price: product.price,
          product_image: product.images?.[0]?.image,
          vendor_name: product.vendor?.business_name,
          quantity: 1,
        });
        toast.success('Added to cart!');
      }
    }
  };

  const handleRemove = (wishlistId: string, productId: string) => {
    removeFromWishlistMutation.mutate({ wishlistId, productId });
  };

  const wishlistItems = Array.isArray(wishlists) ? wishlists : wishlists?.results || [];
  const defaultWishlist = wishlistItems[0];
  const products = defaultWishlist?.products || [];

  return (
    <div className="container py-8">
      {/* Back Link */}
      <Link
        href="/account/profile"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Profile
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">My Wishlist</h1>
        <p className="mt-2 text-muted-foreground">
          Save your favorite items for later
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-96 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : products.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Heart className="h-16 w-16 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">Your wishlist is empty</h2>
            <p className="mt-2 text-center text-muted-foreground">
              Start adding products to your wishlist
            </p>
            <Button className="mt-6" asChild>
              <Link href="/products">Browse Products</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {products.length} {products.length === 1 ? 'item' : 'items'}
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product: any) => (
              <Card key={product.id} className="group overflow-hidden">
                <Link href={`/products/${product.id}`}>
                  <div className="relative aspect-square overflow-hidden bg-muted">
                    {product.images?.[0] ? (
                      <Image
                        src={product.images[0].image}
                        alt={product.name}
                        fill
                        className="object-cover transition-transform group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <Heart className="h-16 w-16 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                </Link>
                <CardContent className="p-4">
                  <Link href={`/products/${product.id}`}>
                    <h3 className="font-semibold line-clamp-2 hover:text-cyan-600">
                      {product.name}
                    </h3>
                  </Link>
                  
                  {product.vendor && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {product.vendor.business_name || 'Unknown Vendor'}
                    </p>
                  )}

                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-lg font-bold text-cyan-600">
                      {formatPrice(product.price)}
                    </span>
                    {product.compare_price && product.compare_price > product.price && (
                      <span className="text-sm text-muted-foreground line-through">
                        {formatPrice(product.compare_price)}
                      </span>
                    )}
                  </div>

                  <div className="mt-4 flex gap-2">
                    <Button
                      size="sm"
                      className="flex-1"
                      onClick={() => handleAddToCart(product)}
                      disabled={addToCartMutation.isPending}
                    >
                      <ShoppingCart className="mr-2 h-4 w-4" />
                      Add to Cart
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRemove(defaultWishlist.id, product.id)}
                      disabled={removeFromWishlistMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

