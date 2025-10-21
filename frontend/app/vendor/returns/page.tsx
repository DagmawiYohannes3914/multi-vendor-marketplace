'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, CheckCircle, XCircle, Eye, ArrowLeft } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { format } from 'date-fns';
import { toast } from 'sonner';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  received: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  refunded: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

export default function VendorReturnsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated } = useAuthStore();
  const [selectedReturn, setSelectedReturn] = useState<any>(null);
  const [vendorNotes, setVendorNotes] = useState('');

  const { data: returns, isLoading } = useQuery({
    queryKey: ['vendor-returns'],
    queryFn: async () => {
      const response = await apiClient.getVendorReturns();
      return response.data;
    },
    enabled: isAuthenticated && user?.is_vendor,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      apiClient.approveReturn(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-returns'] });
      toast.success('Return approved successfully');
      setSelectedReturn(null);
      setVendorNotes('');
    },
    onError: () => {
      toast.error('Failed to approve return');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      apiClient.rejectReturn(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-returns'] });
      toast.success('Return rejected');
      setSelectedReturn(null);
      setVendorNotes('');
    },
    onError: () => {
      toast.error('Failed to reject return');
    },
  });

  if (!isAuthenticated || !user?.is_vendor) {
    router.push('/auth/login');
    return null;
  }

  const returnsList = Array.isArray(returns) ? returns : returns?.results || [];

  return (
    <div className="container py-8">
      {/* Back Link */}
      <Link
        href="/vendor/dashboard"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Return Requests</h1>
        <p className="mt-2 text-muted-foreground">
          Manage customer return requests
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
              You don't have any pending return requests
            </p>
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
                      Order #{returnItem.order?.id?.substring(0, 8)} •{' '}
                      {format(new Date(returnItem.created_at), 'MMM d, yyyy')}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      STATUS_COLORS[returnItem.status] || STATUS_COLORS.pending
                    }`}
                  >
                    {returnItem.status.toUpperCase()}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Return Info */}
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <p className="text-sm font-medium">Customer</p>
                      <p className="text-sm text-muted-foreground">
                        {returnItem.order?.user?.username || returnItem.order?.guest_email || 'Unknown'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Reason</p>
                      <p className="text-sm text-muted-foreground capitalize">
                        {returnItem.reason?.replace('_', ' ')}
                      </p>
                    </div>
                  </div>

                  {/* Description */}
                  {returnItem.description && (
                    <div>
                      <p className="text-sm font-medium">Description</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {returnItem.description}
                      </p>
                    </div>
                  )}

                  {/* Images */}
                  {returnItem.images && returnItem.images.length > 0 && (
                    <div>
                      <p className="mb-2 text-sm font-medium">Attached Images</p>
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

                  {/* Returned Items */}
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
                          <p className="font-medium">{formatPrice(item.unit_price)}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Vendor Notes Section */}
                  {returnItem.status === 'pending' && (
                    <div className="rounded-lg border-2 border-dashed p-4">
                      <p className="mb-2 text-sm font-medium">Vendor Notes (Optional)</p>
                      <textarea
                        value={selectedReturn?.id === returnItem.id ? vendorNotes : ''}
                        onChange={(e) => {
                          setSelectedReturn(returnItem);
                          setVendorNotes(e.target.value);
                        }}
                        placeholder="Add any notes for the customer..."
                        className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                  )}

                  {/* Actions */}
                  {returnItem.status === 'pending' && (
                    <div className="flex gap-2">
                      <Button
                        className="flex-1"
                        onClick={() => {
                          if (selectedReturn?.id === returnItem.id) {
                            approveMutation.mutate({ id: returnItem.id, notes: vendorNotes });
                          } else {
                            setSelectedReturn(returnItem);
                            approveMutation.mutate({ id: returnItem.id, notes: '' });
                          }
                        }}
                        disabled={approveMutation.isPending}
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Approve Return
                      </Button>
                      <Button
                        variant="destructive"
                        className="flex-1"
                        onClick={() => {
                          if (selectedReturn?.id === returnItem.id && vendorNotes.trim()) {
                            rejectMutation.mutate({ id: returnItem.id, notes: vendorNotes });
                          } else {
                            const reason = prompt('Please provide a reason for rejection:');
                            if (reason) {
                              rejectMutation.mutate({ id: returnItem.id, notes: reason });
                            }
                          }
                        }}
                        disabled={rejectMutation.isPending}
                      >
                        <XCircle className="mr-2 h-4 w-4" />
                        Reject Return
                      </Button>
                    </div>
                  )}

                  {/* Vendor Notes Display (if already processed) */}
                  {returnItem.vendor_notes && returnItem.status !== 'pending' && (
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-sm font-medium">Your Notes</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {returnItem.vendor_notes}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

