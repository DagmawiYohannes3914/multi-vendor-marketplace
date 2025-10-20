'use client';

import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useCartStore } from '@/store/cart-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Trash2, Plus, Minus, ShoppingBag, ArrowRight } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { toast } from 'sonner';

export default function CartPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [couponCode, setCouponCode] = useState('');

  // Guest cart from localStorage
  const { guestItems, removeGuestItem, updateGuestItemQuantity, getGuestCartTotal } = useCartStore();

  // Authenticated cart from backend
  const { data: cart, isLoading } = useQuery({
    queryKey: ['cart'],
    queryFn: async () => {
      const response = await apiClient.getCart();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  const updateMutation = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: string; quantity: number }) =>
      apiClient.updateCartItem(itemId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (itemId: string) => apiClient.removeFromCart(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      toast.success('Item removed from cart');
    },
  });

  const handleUpdateQuantity = (itemId: string, currentQty: number, change: number) => {
    const newQty = currentQty + change;
    if (newQty > 0) {
      updateMutation.mutate({ itemId, quantity: newQty });
    }
  };

  const handleRemove = (itemId: string) => {
    removeMutation.mutate(itemId);
  };

  const handleGuestUpdateQuantity = (sku: string, currentQty: number, change: number) => {
    const newQty = currentQty + change;
    if (newQty > 0) {
      updateGuestItemQuantity(sku, newQty);
    }
  };

  const handleGuestRemove = (sku: string) => {
    removeGuestItem(sku);
    toast.success('Item removed from cart');
  };

  const calculateTotal = () => {
    if (isAuthenticated) {
      if (!cart?.items) return 0;
      return cart.items.reduce((total: number, item: any) => {
        return total + parseFloat(item.unit_price) * item.quantity;
      }, 0);
    } else {
      return getGuestCartTotal();
    }
  };

  // Get items based on auth status
  const items = isAuthenticated ? cart?.items : guestItems;

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="h-32 rounded bg-muted" />
          <div className="h-32 rounded bg-muted" />
        </div>
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="container flex min-h-[60vh] flex-col items-center justify-center py-10">
        <ShoppingBag className="h-16 w-16 text-muted-foreground" />
        <h2 className="mt-4 text-2xl font-semibold">Your cart is empty</h2>
        <p className="mt-2 text-muted-foreground">
          Add some products to get started
        </p>
        <Button className="mt-6" asChild>
          <Link href="/products">Browse Products</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold">Shopping Cart</h1>
      
      {!isAuthenticated && (
        <div className="mt-4 rounded-lg bg-blue-50 p-4 dark:bg-blue-950">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <Link href="/auth/login" className="font-semibold underline">
              Login
            </Link>{' '}
            or{' '}
            <Link href="/auth/register" className="font-semibold underline">
              Sign up
            </Link>{' '}
            to save your cart and checkout faster!
          </p>
        </div>
      )}
      
      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {isAuthenticated ? (
            /* Authenticated User Cart */
            cart?.items.map((item: any) => (
              <Card key={item.id}>
                <CardContent className="flex gap-4 p-4">
                  <div className="relative h-24 w-24 overflow-hidden rounded bg-muted">
                    {item.sku_detail?.product?.images?.[0] ? (
                      <Image
                        src={item.sku_detail.product.images[0].image}
                        alt={item.sku_detail.product.name}
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <ShoppingBag className="h-8 w-8 text-muted-foreground" />
                      </div>
                    )}
                  </div>

                  <div className="flex flex-1 flex-col justify-between">
                    <div>
                      <h3 className="font-semibold">
                        {item.sku_detail?.product?.name || 'Product'}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        SKU: {item.sku_detail?.sku_code}
                      </p>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Button
                          size="icon"
                          variant="outline"
                          className="h-8 w-8"
                          onClick={() => handleUpdateQuantity(item.id, item.quantity, -1)}
                          disabled={item.quantity <= 1 || updateMutation.isPending}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <span className="w-12 text-center">{item.quantity}</span>
                        <Button
                          size="icon"
                          variant="outline"
                          className="h-8 w-8"
                          onClick={() => handleUpdateQuantity(item.id, item.quantity, 1)}
                          disabled={updateMutation.isPending}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="flex items-center gap-4">
                        <span className="font-semibold">
                          {formatPrice(parseFloat(item.unit_price) * item.quantity)}
                        </span>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleRemove(item.id)}
                          disabled={removeMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            /* Guest Cart */
            guestItems.map((item: any) => (
              <Card key={item.sku}>
                <CardContent className="flex gap-4 p-4">
                  <div className="relative h-24 w-24 overflow-hidden rounded bg-muted">
                    {item.product_image ? (
                      <Image
                        src={item.product_image}
                        alt={item.product_name}
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <ShoppingBag className="h-8 w-8 text-muted-foreground" />
                      </div>
                    )}
                  </div>

                  <div className="flex flex-1 flex-col justify-between">
                    <div>
                      <h3 className="font-semibold">{item.product_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {item.vendor_name || 'Vendor Store'}
                      </p>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Button
                          size="icon"
                          variant="outline"
                          className="h-8 w-8"
                          onClick={() => handleGuestUpdateQuantity(item.sku, item.quantity, -1)}
                          disabled={item.quantity <= 1}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <span className="w-12 text-center">{item.quantity}</span>
                        <Button
                          size="icon"
                          variant="outline"
                          className="h-8 w-8"
                          onClick={() => handleGuestUpdateQuantity(item.sku, item.quantity, 1)}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="flex items-center gap-4">
                        <span className="font-semibold">
                          {formatPrice(parseFloat(item.product_price) * item.quantity)}
                        </span>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleGuestRemove(item.sku)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal ({items.length} items)</span>
                  <span>{formatPrice(calculateTotal())}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Shipping</span>
                  <span>Calculated at checkout</span>
                </div>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between font-semibold">
                  <span>Total</span>
                  <span>{formatPrice(calculateTotal())}</span>
                </div>
              </div>

              <Button className="w-full" size="lg" asChild>
                <Link href="/checkout">
                  Proceed to Checkout <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>

              <Button variant="outline" className="w-full" asChild>
                <Link href="/products">Continue Shopping</Link>
              </Button>

              {/* Coupon Code */}
              <div className="border-t pt-4">
                <label className="text-sm font-medium">Coupon Code</label>
                <div className="mt-2 flex gap-2">
                  <input
                    type="text"
                    placeholder="Enter code"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value)}
                    className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                  <Button variant="outline">Apply</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

