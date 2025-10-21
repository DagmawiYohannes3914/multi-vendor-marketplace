'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import Image from 'next/image';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useCartStore } from '@/store/cart-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Flame, ShoppingCart, Clock, TrendingUp } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { toast } from 'sonner';
import { useEffect, useState } from 'react';
import { format, differenceInSeconds } from 'date-fns';

export default function FlashSalesPage() {
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const addGuestItem = useCartStore((state) => state.addGuestItem);

  const { data: flashSales, isLoading } = useQuery({
    queryKey: ['flash-sales'],
    queryFn: async () => {
      const response = await apiClient.getLiveFlashSales();
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

  const flashSalesList = Array.isArray(flashSales) ? flashSales : flashSales?.results || [];

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <Flame className="h-10 w-10 text-orange-500" />
          <div>
            <h1 className="text-3xl font-bold">Flash Sales</h1>
            <p className="text-muted-foreground">Limited time offers - don't miss out!</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-96 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : flashSalesList.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Flame className="h-16 w-16 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">No Active Flash Sales</h2>
            <p className="mt-2 text-center text-muted-foreground">
              Check back soon for amazing deals!
            </p>
            <Button className="mt-6" asChild>
              <Link href="/products">Browse All Products</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {flashSalesList.map((sale: any) => {
            const product = sale.product;
            const originalPrice = parseFloat(product.price);
            const salePrice = parseFloat(sale.sale_price);
            const discount = Math.round(((originalPrice - salePrice) / originalPrice) * 100);

            return (
              <Card key={sale.id} className="group overflow-hidden">
                <div className="relative">
                  {/* Flash Sale Badge */}
                  <div className="absolute left-2 top-2 z-10 flex items-center gap-1 rounded-full bg-orange-500 px-3 py-1 text-xs font-bold text-white">
                    <Flame className="h-3 w-3" />
                    {discount}% OFF
                  </div>

                  {/* Countdown Timer */}
                  <CountdownTimer endTime={sale.end_time} />

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
                          <ShoppingCart className="h-16 w-16 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  </Link>
                </div>

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
                    <span className="text-xl font-bold text-orange-600">
                      {formatPrice(salePrice)}
                    </span>
                    <span className="text-sm text-muted-foreground line-through">
                      {formatPrice(originalPrice)}
                    </span>
                  </div>

                  {sale.stock_limit > 0 && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Only {sale.stock_limit} left</span>
                        <span>
                          <TrendingUp className="inline h-3 w-3" /> Popular
                        </span>
                      </div>
                      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-orange-500"
                          style={{
                            width: `${Math.min(
                              100,
                              ((sale.stock_limit - (sale.stock_remaining || sale.stock_limit)) /
                                sale.stock_limit) *
                                100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <Button
                    className="mt-4 w-full bg-orange-600 hover:bg-orange-700"
                    onClick={() => handleAddToCart(product)}
                    disabled={addToCartMutation.isPending}
                  >
                    <ShoppingCart className="mr-2 h-4 w-4" />
                    Add to Cart
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function CountdownTimer({ endTime }: { endTime: string }) {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const end = new Date(endTime);
      const seconds = differenceInSeconds(end, now);

      if (seconds <= 0) {
        setTimeLeft('Ended');
        return;
      }

      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = seconds % 60;

      setTimeLeft(`${hours}h ${minutes}m ${secs}s`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [endTime]);

  return (
    <div className="absolute right-2 top-2 z-10 flex items-center gap-1 rounded-full bg-black/70 px-3 py-1 text-xs font-medium text-white backdrop-blur-sm">
      <Clock className="h-3 w-3" />
      {timeLeft}
    </div>
  );
}

