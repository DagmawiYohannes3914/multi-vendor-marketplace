'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { StarRating } from '@/components/star-rating';
import { Card, CardContent } from '@/components/ui/card';
import { Store } from 'lucide-react';
import Link from 'next/link';

interface VendorRatingProps {
  vendorId: string;
  vendorName: string;
  showReviews?: boolean;
}

export function VendorRating({ vendorId, vendorName, showReviews = false }: VendorRatingProps) {
  const { data: vendor } = useQuery({
    queryKey: ['vendor', vendorId],
    queryFn: async () => {
      const response = await apiClient.getVendorProfile(vendorId);
      return response.data;
    },
  });

  const { data: reviews } = useQuery({
    queryKey: ['vendor-reviews', vendorId],
    queryFn: async () => {
      const response = await apiClient.getVendorReviews(vendorId);
      return response.data;
    },
    enabled: showReviews,
  });

  const averageRating = vendor?.average_rating || 0;
  const totalReviews = vendor?.total_reviews || 0;
  const reviewsList = Array.isArray(reviews) ? reviews : reviews?.results || [];

  return (
    <div className="space-y-4">
      {/* Vendor Rating Summary */}
      <Card>
        <CardContent className="flex items-center gap-4 pt-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <Store className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <Link
              href={`/vendor/${vendorId}`}
              className="font-semibold hover:underline"
            >
              {vendorName}
            </Link>
            <div className="mt-1 flex items-center gap-2">
              <StarRating rating={averageRating} size="sm" showValue />
              {totalReviews > 0 && (
                <span className="text-xs text-muted-foreground">
                  ({totalReviews} {totalReviews === 1 ? 'review' : 'reviews'})
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Vendor Reviews List */}
      {showReviews && reviewsList.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold">Vendor Reviews</h3>
          {reviewsList.slice(0, 3).map((review: any) => (
            <Card key={review.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">
                        {review.customer?.username || 'Anonymous'}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {review.review_text}
                    </p>
                  </div>
                  <StarRating rating={review.rating} size="sm" />
                </div>
              </CardContent>
            </Card>
          ))}
          {reviewsList.length > 3 && (
            <Link
              href={`/vendor/${vendorId}`}
              className="block text-center text-sm text-primary hover:underline"
            >
              View all {totalReviews} reviews
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

