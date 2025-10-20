'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { X, Upload, Package } from 'lucide-react';
import { toast } from 'sonner';

interface ReturnRequestDialogProps {
  orderId: string;
  orderNumber: string;
  vendorOrderId: string;
  orderItems: any[];
  onClose: () => void;
  onSuccess?: () => void;
}

const RETURN_REASONS = [
  { value: 'defective', label: 'Defective or Damaged' },
  { value: 'wrong_item', label: 'Wrong Item Sent' },
  { value: 'not_as_described', label: 'Not As Described' },
  { value: 'changed_mind', label: 'Changed Mind' },
  { value: 'size_issue', label: 'Size/Fit Issue' },
  { value: 'other', label: 'Other Reason' },
];

export function ReturnRequestDialog({
  orderId,
  orderNumber,
  vendorOrderId,
  orderItems,
  onClose,
  onSuccess,
}: ReturnRequestDialogProps) {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [reason, setReason] = useState('');
  const [description, setDescription] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const createReturnMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.createReturn(data);
      const returnId = response.data.id;

      // Upload images if any
      if (images.length > 0) {
        await Promise.all(
          images.map((image) => apiClient.uploadReturnImage(returnId, image))
        );
      }

      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['order', orderId] });
      queryClient.invalidateQueries({ queryKey: ['returns'] });
      toast.success('Return request submitted successfully!');
      onSuccess?.();
      onClose();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to submit return request';
      toast.error(errorMessage);
    },
  });

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length + images.length > 5) {
      toast.error('Maximum 5 images allowed');
      return;
    }

    setImages((prev) => [...prev, ...files]);
    const newPreviewUrls = files.map((file) => URL.createObjectURL(file));
    setPreviewUrls((prev) => [...prev, ...newPreviewUrls]);
  };

  const handleRemoveImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
    URL.revokeObjectURL(previewUrls[index]);
    setPreviewUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const toggleItem = (itemId: string) => {
    setSelectedItems((prev) =>
      prev.includes(itemId)
        ? prev.filter((id) => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedItems.length === 0) {
      toast.error('Please select at least one item to return');
      return;
    }

    if (!reason) {
      toast.error('Please select a reason for return');
      return;
    }

    if (description.trim().length < 20) {
      toast.error('Please provide more details (minimum 20 characters)');
      return;
    }

    createReturnMutation.mutate({
      order: orderId,
      vendor_order: vendorOrderId,
      items: selectedItems,
      reason,
      description: description.trim(),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <Card className="w-full max-w-2xl my-8">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Request Return - Order #{orderNumber}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Select Items */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Select Items to Return *</label>
              <div className="space-y-2">
                {orderItems.map((item) => (
                  <label
                    key={item.id}
                    className="flex cursor-pointer items-center gap-3 rounded-lg border p-3 hover:bg-accent"
                  >
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.id)}
                      onChange={() => toggleItem(item.id)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <div className="flex-1">
                      <p className="font-medium">{item.product?.name || 'Product'}</p>
                      <p className="text-sm text-muted-foreground">
                        Quantity: {item.quantity} × ${parseFloat(item.unit_price).toFixed(2)}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Reason Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason for Return *</label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                required
              >
                <option value="">Select a reason...</option>
                {RETURN_REASONS.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium">
                Detailed Description *
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Please describe the issue in detail (e.g., what's wrong, damage description, etc.)"
                className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                required
              />
              <p className="text-xs text-muted-foreground">
                {description.length} characters (minimum 20 required)
              </p>
            </div>

            {/* Image Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Add Photos (Optional but Recommended)
              </label>
              <p className="text-xs text-muted-foreground">
                Photos help us process your return faster (max 5)
              </p>
              
              <div className="flex flex-wrap gap-4">
                {previewUrls.map((url, index) => (
                  <div key={index} className="relative h-24 w-24">
                    <img
                      src={url}
                      alt={`Preview ${index + 1}`}
                      className="h-full w-full rounded-lg object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(index)}
                      className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}

                {images.length < 5 && (
                  <label className="flex h-24 w-24 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 hover:border-muted-foreground/50">
                    <Upload className="h-6 w-6 text-muted-foreground" />
                    <span className="mt-1 text-xs text-muted-foreground">Upload</span>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={handleImageSelect}
                      className="hidden"
                    />
                  </label>
                )}
              </div>
            </div>

            {/* Info Box */}
            <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-200">
              <p className="font-semibold">Return Process:</p>
              <ul className="mt-2 list-inside list-disc space-y-1">
                <li>Your request will be reviewed within 24-48 hours</li>
                <li>You'll receive a return shipping label via email</li>
                <li>Refund will be processed after item inspection</li>
                <li>Refunds typically take 5-7 business days</li>
              </ul>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={createReturnMutation.isPending}
                className="flex-1"
              >
                {createReturnMutation.isPending ? 'Submitting...' : 'Submit Return Request'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

