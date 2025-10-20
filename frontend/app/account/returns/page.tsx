'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, Eye, ArrowLeft } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { format } from 'date-fns';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  received: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  refunded: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  completed: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending Review',
  approved: 'Approved',
  rejected: 'Rejected',
  received: 'Item Received',
  refunded: 'Refunded',
  completed: 'Completed',
};

export default function ReturnsPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const { data: returns, isLoading } = useQuery({
    queryKey: ['returns'],
    queryFn: async () => {
      const response = await apiClient.getReturns();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) {
    router.push('/auth/login');
    return null;
  }

  const returnsList = Array.isArray(returns) ? returns : returns?.results || [];

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

      <div className="mb-8">
        <h1 className="text-3xl font-bold">My Returns</h1>
        <p className="mt-2 text-muted-foreground">
          Track and manage your return requests
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : returnsList.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Package className="h-16 w-16 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">No Return Requests</h2>
            <p className="mt-2 text-center text-muted-foreground">
              You haven't requested any returns yet
            </p>
            <Button className="mt-6" asChild>
              <Link href="/account/orders">View Your Orders</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {returnsList.map((returnItem: any) => (
            <Card key={returnItem.id}>
              <CardHeader>
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <CardTitle>RMA #{returnItem.rma_number}</CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Order #{returnItem.order?.id?.substring(0, 8)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${
                        STATUS_COLORS[returnItem.status] || STATUS_COLORS.pending
                      }`}
                    >
                      {STATUS_LABELS[returnItem.status] || returnItem.status}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Return Info */}
                  <div className="grid gap-4 text-sm sm:grid-cols-2">
                    <div>
                      <p className="text-muted-foreground">Requested On</p>
                      <p className="font-medium">
                        {format(new Date(returnItem.created_at), 'MMM d, yyyy')}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Reason</p>
                      <p className="font-medium capitalize">
                        {returnItem.reason?.replace('_', ' ')}
                      </p>
                    </div>
                    {returnItem.refund_amount > 0 && (
                      <div>
                        <p className="text-muted-foreground">Refund Amount</p>
                        <p className="font-medium">
                          {formatPrice(returnItem.refund_amount)}
                        </p>
                      </div>
                    )}
                    {returnItem.approved_at && (
                      <div>
                        <p className="text-muted-foreground">Approved On</p>
                        <p className="font-medium">
                          {format(new Date(returnItem.approved_at), 'MMM d, yyyy')}
                        </p>
                      </div>
                    )}
                    {returnItem.refunded_at && (
                      <div>
                        <p className="text-muted-foreground">Refunded On</p>
                        <p className="font-medium">
                          {format(new Date(returnItem.refunded_at), 'MMM d, yyyy')}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  {returnItem.description && (
                    <div>
                      <p className="text-sm text-muted-foreground">Description</p>
                      <p className="mt-1 text-sm">{returnItem.description}</p>
                    </div>
                  )}

                  {/* Vendor Notes */}
                  {returnItem.vendor_notes && (
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-sm font-medium">Vendor Response</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {returnItem.vendor_notes}
                      </p>
                    </div>
                  )}

                  {/* Images */}
                  {returnItem.images && returnItem.images.length > 0 && (
                    <div>
                      <p className="mb-2 text-sm text-muted-foreground">Attached Images</p>
                      <div className="flex gap-2">
                        {returnItem.images.map((image: string, index: number) => (
                          <img
                            key={index}
                            src={image}
                            alt={`Return evidence ${index + 1}`}
                            className="h-20 w-20 rounded-lg object-cover"
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Items */}
                  <div>
                    <p className="mb-2 text-sm font-medium">Returned Items</p>
                    <div className="space-y-2">
                      {returnItem.items?.map((item: any) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between rounded-lg border p-3"
                        >
                          <div>
                            <p className="font-medium">{item.product?.name || 'Product'}</p>
                            <p className="text-sm text-muted-foreground">
                              Qty: {item.quantity}
                            </p>
                          </div>
                          <p className="font-medium">
                            {formatPrice(item.unit_price)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Status Timeline */}
                  <div className="rounded-lg border-l-4 border-primary bg-muted/50 p-4">
                    <p className="text-sm font-medium">Status Updates</p>
                    <div className="mt-3 space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-green-500" />
                        <span className="text-muted-foreground">
                          Return request submitted
                        </span>
                      </div>
                      {returnItem.approved_at && (
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500" />
                          <span className="text-muted-foreground">
                            Approved by vendor
                          </span>
                        </div>
                      )}
                      {returnItem.received_at && (
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500" />
                          <span className="text-muted-foreground">
                            Item received by vendor
                          </span>
                        </div>
                      )}
                      {returnItem.refunded_at && (
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500" />
                          <span className="text-muted-foreground">
                            Refund processed
                          </span>
                        </div>
                      )}
                      {returnItem.status === 'rejected' && (
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-red-500" />
                          <span className="text-muted-foreground">
                            Return request rejected
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

