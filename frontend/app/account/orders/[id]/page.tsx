'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Download, Package, MapPin, CreditCard, Truck } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { format } from 'date-fns';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  paid: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  shipped: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  delivered: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  cancelled: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export default function OrderDetailPage() {
  const router = useRouter();
  const params = useParams();
  const orderId = Array.isArray(params.id) ? params.id[0] : params.id;
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const { data: order, isLoading } = useQuery({
    queryKey: ['order', orderId],
    queryFn: async () => {
      const response = await apiClient.getOrders();
      const orders = Array.isArray(response.data) ? response.data : response.data.results || [];
      return orders.find((o: any) => o.id === orderId);
    },
    enabled: isAuthenticated && !!orderId,
  });

  const handleDownloadReceipt = async () => {
    try {
      const response = await apiClient.getOrderReceipt(orderId);
      // Create a blob and download
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt-${orderId.substring(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download receipt:', error);
    }
  };

  if (!isAuthenticated) {
    router.push('/auth/login');
    return null;
  }

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="h-96 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container py-8">
        <Card>
          <CardContent className="py-16 text-center">
            <Package className="mx-auto h-16 w-16 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">Order not found</h2>
            <Button className="mt-6" asChild>
              <Link href="/account/orders">Back to Orders</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container py-8">
      {/* Back Link */}
      <Link
        href="/account/orders"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Orders
      </Link>

      {/* Order Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Order #{order.id.substring(0, 8)}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Placed on {format(new Date(order.created_at), 'MMMM d, yyyy')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownloadReceipt}>
            <Download className="mr-2 h-4 w-4" />
            Download Receipt
          </Button>
          <span
            className={`flex items-center rounded-full px-4 py-2 text-sm font-medium ${
              STATUS_COLORS[order.status] || STATUS_COLORS.pending
            }`}
          >
            {order.status.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Order Items */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Order Items
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {order.vendor_orders?.map((vendorOrder: any) => (
                  <div key={vendorOrder.id} className="space-y-3">
                    <div className="flex items-center justify-between border-b pb-2">
                      <p className="font-semibold">
                        {vendorOrder.vendor?.store_name || 'Unknown Vendor'}
                      </p>
                      <span className="text-sm text-muted-foreground">
                        {vendorOrder.status}
                      </span>
                    </div>
                    {vendorOrder.items?.map((item: any) => (
                      <div key={item.id} className="flex gap-4">
                        <div className="flex-1">
                          <p className="font-medium">{item.product?.name || 'Product'}</p>
                          <p className="text-sm text-muted-foreground">
                            SKU: {item.sku?.sku_code}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Quantity: {item.quantity}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{formatPrice(item.unit_price)}</p>
                          <p className="text-sm text-muted-foreground">
                            Total: {formatPrice(parseFloat(item.unit_price) * item.quantity)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Shipping Address */}
          {order.shipping_address && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Shipping Address
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium">{order.shipping_address.recipient_name}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {order.shipping_address.street_address}
                </p>
                {order.shipping_address.apartment && (
                  <p className="text-sm text-muted-foreground">
                    {order.shipping_address.apartment}
                  </p>
                )}
                <p className="text-sm text-muted-foreground">
                  {order.shipping_address.city}, {order.shipping_address.state}{' '}
                  {order.shipping_address.postal_code}
                </p>
                <p className="text-sm text-muted-foreground">
                  {order.shipping_address.country}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Phone: {order.shipping_address.phone}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Order Summary */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal</span>
                <span>{formatPrice(order.total_amount)}</span>
              </div>
              {order.discount_amount > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Discount</span>
                  <span className="text-green-600">
                    -{formatPrice(order.discount_amount)}
                  </span>
                </div>
              )}
              <div className="border-t pt-3">
                <div className="flex justify-between font-semibold">
                  <span>Total</span>
                  <span>{formatPrice(order.total_amount)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Payment Method
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm capitalize">
                {order.payment_method?.replace('_', ' ') || 'Not specified'}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Payment Status: {order.payment_status || 'Unknown'}
              </p>
            </CardContent>
          </Card>

          {order.tracking_number && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Tracking
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm font-mono">{order.tracking_number}</p>
                <Button variant="link" className="mt-2 p-0" asChild>
                  <a
                    href={`https://www.google.com/search?q=${order.tracking_number}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Track Package
                  </a>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

