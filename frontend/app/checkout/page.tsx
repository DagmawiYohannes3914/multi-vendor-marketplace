'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useCartStore } from '@/store/cart-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MapPin, CreditCard, Package, User, Truck } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { toast } from 'sonner';
import { ShippingRates } from '@/components/shipping-rates';

export default function CheckoutPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const guestItems = useCartStore((state) => state.guestItems);
  const clearGuestCart = useCartStore((state) => state.clearGuestCart);
  
  // Authenticated user states
  const [selectedAddress, setSelectedAddress] = useState<string>('');
  
  // Guest user states
  const [guestEmail, setGuestEmail] = useState('');
  const [guestShipping, setGuestShipping] = useState({
    recipient_name: '',
    phone: '',
    street_address: '',
    apartment: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'USA',
  });
  
  const [paymentMethod, setPaymentMethod] = useState('cash_on_delivery');
  const [selectedShippingRate, setSelectedShippingRate] = useState<string | null>(null);
  const [shippingCost, setShippingCost] = useState(0);

  const handleSelectShippingRate = (rateId: string, cost: number) => {
    setSelectedShippingRate(rateId);
    setShippingCost(cost);
  };

  const { data: cart } = useQuery({
    queryKey: ['cart'],
    queryFn: async () => {
      const response = await apiClient.getCart();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  const { data: addresses } = useQuery({
    queryKey: ['addresses'],
    queryFn: async () => {
      const response = await apiClient.getShippingAddresses();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  const checkoutMutation = useMutation({
    mutationFn: (data: any) => apiClient.checkout(data),
    onSuccess: (response) => {
      const data = response.data;
      
      // Clear guest cart if guest checkout
      if (!isAuthenticated) {
        clearGuestCart();
      }
      
      // Handle Stripe redirect
      if (data.checkout_url) {
        toast.success('Redirecting to payment...');
        window.location.href = data.checkout_url;
        return;
      }
      
      // Handle COD (immediate order creation)
      if (data.order_id) {
        toast.success('Order placed successfully!');
        toast.success('Order confirmation sent to your email!');
        
        // Redirect based on user type
        if (isAuthenticated) {
          router.push('/account/orders');
        } else {
          router.push('/');
        }
      }
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Checkout failed';
      toast.error(errorMessage);
      console.error('Checkout error:', error.response?.data);
    },
  });

  const handleCheckout = async () => {
    if (isAuthenticated) {
      // Authenticated checkout
      if (!selectedAddress) {
        toast.error('Please select a shipping address');
        return;
      }

      const address = addresses?.find((a: any) => a.id === selectedAddress);
      
      const checkoutData = {
        payment_method: paymentMethod,
        shipping_address: {
          recipient_name: address.recipient_name,
          phone: address.phone,
          street_address: address.street_address,
          apartment: address.apartment,
          city: address.city,
          state: address.state,
          postal_code: address.postal_code,
          country: address.country,
        },
      };

      checkoutMutation.mutate(checkoutData);
    } else {
      // Guest checkout
      if (!guestEmail || !guestShipping.recipient_name || !guestShipping.phone || 
          !guestShipping.street_address || !guestShipping.city || 
          !guestShipping.state || !guestShipping.postal_code) {
        toast.error('Please fill in all required fields');
        return;
      }

      // Prepare guest checkout data for backend
      const guestCheckoutData = {
        is_guest: true,
        guest_email: guestEmail,
        guest_name: guestShipping.recipient_name,
        guest_phone: guestShipping.phone,
        items: guestItems.map((item) => ({
          sku_id: item.sku_id,  // SKU UUID for backend
          quantity: item.quantity,
        })),
        shipping_address: guestShipping,
        payment_method: paymentMethod,
      };

      checkoutMutation.mutate(guestCheckoutData);
    }
  };

  const calculateTotal = () => {
    if (isAuthenticated) {
      if (!cart?.items) return 0;
      return cart.items.reduce((total: number, item: any) => {
        return total + parseFloat(item.unit_price) * item.quantity;
      }, 0);
    } else {
      return guestItems.reduce((total, item) => {
        return total + parseFloat(item.product_price) * item.quantity;
      }, 0);
    }
  };

  const items = isAuthenticated ? cart?.items : guestItems;

  if (!items || items.length === 0) {
    router.push('/cart');
    return null;
  }

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold">Checkout</h1>

      {!isAuthenticated && (
        <div className="mt-4 rounded-lg bg-blue-50 p-4 dark:bg-blue-950">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            Have an account?{' '}
            <Link href="/auth/login" className="font-semibold underline">
              Login
            </Link>{' '}
            for faster checkout with saved addresses!
          </p>
        </div>
      )}

      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        {/* Checkout Steps */}
        <div className="lg:col-span-2 space-y-6">
          {isAuthenticated ? (
            /* Authenticated User - Saved Addresses */
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Shipping Address
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {addresses && addresses.length > 0 ? (
                  <div className="space-y-2">
                    {addresses.map((address: any) => (
                      <label
                        key={address.id}
                        className="flex cursor-pointer items-start gap-3 rounded-lg border p-4 hover:bg-accent"
                      >
                        <input
                          type="radio"
                          name="address"
                          value={address.id}
                          checked={selectedAddress === address.id}
                          onChange={(e) => setSelectedAddress(e.target.value)}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <p className="font-semibold">{address.label}</p>
                          <p className="text-sm text-muted-foreground">
                            {address.recipient_name}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {address.street_address}
                            {address.apartment && `, ${address.apartment}`}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {address.city}, {address.state} {address.postal_code}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {address.phone}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">No addresses saved</p>
                    <Button className="mt-4" asChild>
                      <a href="/account/addresses">Add Address</a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            /* Guest User - Shipping Form */
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Contact Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Email</label>
                    <input
                      type="email"
                      placeholder="you@example.com"
                      value={guestEmail}
                      onChange={(e) => setGuestEmail(e.target.value)}
                      required
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="h-5 w-5" />
                    Shipping Address
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Full Name *</label>
                      <input
                        type="text"
                        value={guestShipping.recipient_name}
                        onChange={(e) =>
                          setGuestShipping({ ...guestShipping, recipient_name: e.target.value })
                        }
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Phone Number *</label>
                      <input
                        type="tel"
                        value={guestShipping.phone}
                        onChange={(e) =>
                          setGuestShipping({ ...guestShipping, phone: e.target.value })
                        }
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Street Address *</label>
                      <input
                        type="text"
                        value={guestShipping.street_address}
                        onChange={(e) =>
                          setGuestShipping({ ...guestShipping, street_address: e.target.value })
                        }
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Apartment, suite, etc. (Optional)</label>
                      <input
                        type="text"
                        value={guestShipping.apartment}
                        onChange={(e) =>
                          setGuestShipping({ ...guestShipping, apartment: e.target.value })
                        }
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>

                    <div className="grid gap-4 sm:grid-cols-3">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">City *</label>
                        <input
                          type="text"
                          value={guestShipping.city}
                          onChange={(e) =>
                            setGuestShipping({ ...guestShipping, city: e.target.value })
                          }
                          required
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">State *</label>
                        <input
                          type="text"
                          value={guestShipping.state}
                          onChange={(e) =>
                            setGuestShipping({ ...guestShipping, state: e.target.value })
                          }
                          required
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">ZIP Code *</label>
                        <input
                          type="text"
                          value={guestShipping.postal_code}
                          onChange={(e) =>
                            setGuestShipping({ ...guestShipping, postal_code: e.target.value })
                          }
                          required
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Shipping Method */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Truck className="h-5 w-5" />
                Shipping Method
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ShippingRates
                selectedRate={selectedShippingRate}
                onSelectRate={handleSelectShippingRate}
              />
            </CardContent>
          </Card>

          {/* Payment Method */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Payment Method
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <label className="flex cursor-pointer items-center gap-3 rounded-lg border p-4 hover:bg-accent">
                  <input
                    type="radio"
                    name="payment"
                    value="stripe"
                    checked={paymentMethod === 'stripe'}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                  />
                  <CreditCard className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="font-semibold">Credit/Debit Card</p>
                    <p className="text-sm text-muted-foreground">
                      Pay securely with Stripe
                    </p>
                  </div>
                </label>
                
                <label className="flex cursor-pointer items-center gap-3 rounded-lg border p-4 hover:bg-accent">
                  <input
                    type="radio"
                    name="payment"
                    value="cash_on_delivery"
                    checked={paymentMethod === 'cash_on_delivery'}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                  />
                  <Truck className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="font-semibold">Cash on Delivery</p>
                    <p className="text-sm text-muted-foreground">
                      Pay when you receive your order
                    </p>
                  </div>
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Order Items */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Order Items ({items.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {isAuthenticated
                  ? cart?.items.map((item: any) => (
                      <div key={item.id} className="flex justify-between">
                        <div>
                          <p className="font-medium">
                            {item.sku_detail?.product?.name || 'Product'}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Qty: {item.quantity}
                          </p>
                        </div>
                        <p className="font-semibold">
                          {formatPrice(parseFloat(item.unit_price) * item.quantity)}
                        </p>
                      </div>
                    ))
                  : guestItems.map((item: any) => (
                      <div key={item.sku} className="flex justify-between">
                        <div>
                          <p className="font-medium">{item.product_name}</p>
                          <p className="text-sm text-muted-foreground">
                            Qty: {item.quantity}
                          </p>
                        </div>
                        <p className="font-semibold">
                          {formatPrice(parseFloat(item.product_price) * item.quantity)}
                        </p>
                      </div>
                    ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal</span>
                  <span>{formatPrice(calculateTotal())}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Shipping</span>
                  <span>
                    {shippingCost > 0 ? formatPrice(shippingCost) : 'Select shipping method'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tax</span>
                  <span>Calculated at payment</span>
                </div>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Total</span>
                  <span>{formatPrice(calculateTotal() + shippingCost)}</span>
                </div>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={handleCheckout}
                disabled={
                  checkoutMutation.isPending ||
                  !selectedShippingRate ||
                  (isAuthenticated
                    ? !selectedAddress
                    : !guestEmail ||
                      !guestShipping.recipient_name ||
                      !guestShipping.phone ||
                      !guestShipping.street_address ||
                      !guestShipping.city ||
                      !guestShipping.state ||
                      !guestShipping.postal_code)
                }
              >
                {checkoutMutation.isPending 
                  ? 'Processing...' 
                  : !selectedShippingRate 
                    ? 'Select Shipping Method' 
                    : 'Place Order'}
              </Button>

              {!selectedShippingRate && !checkoutMutation.isPending && (
                <p className="mt-2 text-center text-sm text-orange-600 dark:text-orange-400">
                  Please select a shipping method to continue
                </p>
              )}

              <p className="text-xs text-center text-muted-foreground">
                By placing your order, you agree to our terms and conditions
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

