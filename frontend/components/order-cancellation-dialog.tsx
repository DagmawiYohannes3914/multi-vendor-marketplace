'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { X, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

interface OrderCancellationDialogProps {
  orderId: string;
  orderNumber: string;
  onClose: () => void;
  onSuccess?: () => void;
}

const CANCELLATION_REASONS = [
  { value: 'customer_request', label: 'Changed my mind' },
  { value: 'found_better_price', label: 'Found a better price elsewhere' },
  { value: 'ordered_by_mistake', label: 'Ordered by mistake' },
  { value: 'delivery_too_slow', label: 'Delivery taking too long' },
  { value: 'other', label: 'Other reason' },
];

export function OrderCancellationDialog({
  orderId,
  orderNumber,
  onClose,
  onSuccess,
}: OrderCancellationDialogProps) {
  const [reason, setReason] = useState('');
  const [details, setDetails] = useState('');
  const queryClient = useQueryClient();

  const cancelOrderMutation = useMutation({
    mutationFn: (data: any) => apiClient.requestCancellation(orderId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['order', orderId] });
      toast.success('Cancellation request submitted successfully!');
      onSuccess?.();
      onClose();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to submit cancellation request';
      toast.error(errorMessage);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!reason) {
      toast.error('Please select a reason for cancellation');
      return;
    }

    if (reason === 'other' && details.trim().length < 10) {
      toast.error('Please provide more details (minimum 10 characters)');
      return;
    }

    cancelOrderMutation.mutate({
      reason,
      details: details.trim(),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Cancel Order #{orderNumber}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Warning Message */}
            <div className="rounded-lg bg-orange-50 p-4 text-sm text-orange-800 dark:bg-orange-900/20 dark:text-orange-200">
              <p className="font-semibold">Important:</p>
              <ul className="mt-2 list-inside list-disc space-y-1">
                <li>Once cancelled, this action cannot be undone</li>
                <li>Refund will be processed within 5-7 business days</li>
                <li>You will receive a confirmation email</li>
              </ul>
            </div>

            {/* Reason Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason for Cancellation *</label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                required
              >
                <option value="">Select a reason...</option>
                {CANCELLATION_REASONS.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Additional Details */}
            <div className="space-y-2">
              <label htmlFor="details" className="text-sm font-medium">
                Additional Details {reason === 'other' && '*'}
              </label>
              <textarea
                id="details"
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Please provide any additional information..."
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                required={reason === 'other'}
              />
              {reason === 'other' && (
                <p className="text-xs text-muted-foreground">
                  {details.length} characters (minimum 10 required)
                </p>
              )}
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4">
              <Button
                type="submit"
                variant="destructive"
                disabled={cancelOrderMutation.isPending}
                className="flex-1"
              >
                {cancelOrderMutation.isPending ? 'Submitting...' : 'Confirm Cancellation'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Keep Order
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

