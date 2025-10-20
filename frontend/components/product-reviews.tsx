'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { StarRating } from '@/components/star-rating';
import { ReviewForm } from '@/components/review-form';
import { ThumbsUp, ThumbsDown, Image as ImageIcon } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

interface ProductReviewsProps {
  productId: string;
}

export function ProductReviews({ productId }: ProductReviewsProps) {
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [lightboxIndex, setLightboxIndex] = useState(0);
  const [showLightbox, setShowLightbox] = useState(false);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();

  const { data: reviews, isLoading } = useQuery({
    queryKey: ['reviews', productId],
    queryFn: async () => {
      const response = await apiClient.getReviews(productId);
      return response.data;
    },
  });

  const voteReviewMutation = useMutation({
    mutationFn: ({ reviewId, voteType }: { reviewId: string; voteType: 'helpful' | 'not_helpful' }) =>
      apiClient.voteReview(reviewId, voteType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews', productId] });
      toast.success('Thank you for your feedback!');
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to vote';
      toast.error(errorMessage);
    },
  });

  const handleVote = (reviewId: string, voteType: 'helpful' | 'not_helpful') => {
    if (!isAuthenticated) {
      toast.error('Please login to vote on reviews');
      return;
    }
    voteReviewMutation.mutate({ reviewId, voteType });
  };

  const openLightbox = (images: string[], index: number) => {
    setSelectedImages(images);
    setLightboxIndex(index);
    setShowLightbox(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  const reviewsList = Array.isArray(reviews) ? reviews : reviews?.results || [];
  const totalReviews = reviewsList.length;
  const averageRating = totalReviews > 0
    ? reviewsList.reduce((sum: number, r: any) => sum + r.rating, 0) / totalReviews
    : 0;

  return (
    <div className="space-y-6">
      {/* Reviews Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Customer Reviews</h2>
          {totalReviews > 0 && (
            <div className="mt-2 flex items-center gap-3">
              <StarRating rating={averageRating} showValue />
              <span className="text-sm text-muted-foreground">
                Based on {totalReviews} {totalReviews === 1 ? 'review' : 'reviews'}
              </span>
            </div>
          )}
        </div>
        {isAuthenticated && (
          <Button onClick={() => setShowReviewForm(!showReviewForm)}>
            {showReviewForm ? 'Cancel' : 'Write a Review'}
          </Button>
        )}
      </div>

      {/* Review Form */}
      {showReviewForm && (
        <ReviewForm
          productId={productId}
          onSuccess={() => setShowReviewForm(false)}
          onCancel={() => setShowReviewForm(false)}
        />
      )}

      {/* Reviews List */}
      {totalReviews === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              No reviews yet. Be the first to review this product!
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {reviewsList.map((review: any) => (
            <Card key={review.id}>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  {/* Review Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          {review.user?.username?.[0]?.toUpperCase() || 'A'}
                        </div>
                        <div>
                          <p className="font-semibold">
                            {review.user?.username || 'Anonymous'}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {format(new Date(review.created_at), 'MMM d, yyyy')}
                          </p>
                        </div>
                      </div>
                    </div>
                    <StarRating rating={review.rating} />
                  </div>

                  {/* Review Text */}
                  <p className="text-sm leading-relaxed">{review.review}</p>

                  {/* Review Images */}
                  {review.images && review.images.length > 0 && (
                    <div className="flex gap-2">
                      {review.images.map((image: any, index: number) => (
                        <button
                          key={image.id}
                          onClick={() => openLightbox(review.images.map((img: any) => img.image), index)}
                          className="relative h-20 w-20 overflow-hidden rounded-lg border hover:opacity-80"
                        >
                          <img
                            src={image.image}
                            alt={`Review image ${index + 1}`}
                            className="h-full w-full object-cover"
                          />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                            <ImageIcon className="h-5 w-5 text-white" />
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Voting */}
                  <div className="flex items-center gap-4 border-t pt-4">
                    <span className="text-sm text-muted-foreground">Was this helpful?</span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleVote(review.id, 'helpful')}
                        disabled={voteReviewMutation.isPending}
                        className="gap-2"
                      >
                        <ThumbsUp className="h-4 w-4" />
                        Helpful {review.helpful_count > 0 && `(${review.helpful_count})`}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleVote(review.id, 'not_helpful')}
                        disabled={voteReviewMutation.isPending}
                        className="gap-2"
                      >
                        <ThumbsDown className="h-4 w-4" />
                        Not Helpful {review.not_helpful_count > 0 && `(${review.not_helpful_count})`}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Image Lightbox */}
      {showLightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
          onClick={() => setShowLightbox(false)}
        >
          <button
            className="absolute right-4 top-4 text-white"
            onClick={() => setShowLightbox(false)}
          >
            ✕
          </button>
          <img
            src={selectedImages[lightboxIndex]}
            alt="Review"
            className="max-h-[90vh] max-w-[90vw] object-contain"
            onClick={(e) => e.stopPropagation()}
          />
          {selectedImages.length > 1 && (
            <>
              <button
                className="absolute left-4 top-1/2 -translate-y-1/2 text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxIndex((prev) => (prev - 1 + selectedImages.length) % selectedImages.length);
                }}
              >
                ‹
              </button>
              <button
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxIndex((prev) => (prev + 1) % selectedImages.length);
                }}
              >
                ›
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

