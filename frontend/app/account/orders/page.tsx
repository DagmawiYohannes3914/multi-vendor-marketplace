'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, Eye, Download, RotateCcw, XCircle } from 'lucide-react';
import { formatPrice, formatDate } from '@/lib/utils';
import { OrderCancellationDialog } from '@/components/order-cancellation-dialog';
import { ReturnRequestDialog } from '@/components/return-request-dialog';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  paid: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  shipped: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  delivered: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  cancelled: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export default function OrdersPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [cancelOrderId, setCancelOrderId] = useState<string | null>(null);
  const [returnOrderData, setReturnOrderData] = useState<any>(null);

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      const response = await apiClient.getOrders();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) {
    router.push('/auth/login');
    return null;
  }

  const canCancelOrder = (order: any) => {
    return ['pending', 'paid'].includes(order.status);
  };

  const canReturnOrder = (order: any) => {
    return order.status === 'delivered';
  };

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">My Orders</h1>
        <p className="mt-2 text-muted-foreground">
          View and manage your orders
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="h-32 p-6" />
            </Card>
          ))}
        </div>
      ) : orders && orders.length > 0 ? (
        <div className="space-y-4">
          {orders.map((order: any) => (
            <Card key={order.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Order #{order.id.slice(0, 8)}
                  </CardTitle>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      STATUS_COLORS[order.status] || STATUS_COLORS.pending
                    }`}
                  >
                    {order.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Placed on {formatDate(order.created_at)}
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Order Items */}
                  <div className="space-y-2">
                    {order.vendor_orders?.map((vendorOrder: any) =>
                      vendorOrder.items?.map((item: any) => (
                        <div key={item.id} className="flex justify-between text-sm">
                          <span>
                            {item.product?.name || 'Product'} x {item.quantity}
                          </span>
                          <span className="font-medium">
                            {formatPrice(item.unit_price)}
                          </span>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Order Total */}
                  <div className="border-t pt-4">
                    <div className="flex justify-between font-semibold">
                      <span>Total</span>
                      <span>{formatPrice(order.total_amount)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/account/orders/${order.id}`}>
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </Link>
                    </Button>
                    {canCancelOrder(order) && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCancelOrderId(order.id)}
                      >
                        <XCircle className="mr-2 h-4 w-4" />
                        Cancel Order
                      </Button>
                    )}
                    {canReturnOrder(order) && order.vendor_orders?.map((vendorOrder: any, index: number) => (
                      <Button
                        key={vendorOrder.id}
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setReturnOrderData({
                            orderId: order.id,
                            orderNumber: order.id.slice(0, 8),
                            vendorOrderId: vendorOrder.id,
                            orderItems: vendorOrder.items || [],
                            vendorName: vendorOrder.vendor?.store_name || `Vendor ${index + 1}`,
                          })
                        }
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        Return from {vendorOrder.vendor?.store_name || `Vendor ${index + 1}`}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Package className="h-16 w-16 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">No orders yet</h2>
            <p className="mt-2 text-muted-foreground">
              Start shopping to see your orders here
            </p>
            <Button className="mt-6" asChild>
              <Link href="/products">Browse Products</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Cancellation Dialog */}
      {cancelOrderId && (
        <OrderCancellationDialog
          orderId={cancelOrderId}
          orderNumber={cancelOrderId.slice(0, 8)}
          onClose={() => setCancelOrderId(null)}
        />
      )}

      {/* Return Dialog */}
      {returnOrderData && (
        <ReturnRequestDialog
          {...returnOrderData}
          onClose={() => setReturnOrderData(null)}
        />
      )}
    </div>
  );
}

