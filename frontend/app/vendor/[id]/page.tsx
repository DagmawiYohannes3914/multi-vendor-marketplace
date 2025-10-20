'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StarRating } from '@/components/star-rating';
import { Store, MapPin, Package, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';

export default function VendorPage() {
  const params = useParams();
  const vendorId = Array.isArray(params.id) ? params.id[0] : params.id;

  const { data: vendor, isLoading: vendorLoading } = useQuery({
    queryKey: ['vendor', vendorId],
    queryFn: async () => {
      const response = await apiClient.getVendorProfile(vendorId);
      return response.data;
    },
  });

  const { data: reviews, isLoading: reviewsLoading } = useQuery({
    queryKey: ['vendor-reviews', vendorId],
    queryFn: async () => {
      const response = await apiClient.getVendorReviews(vendorId);
      return response.data;
    },
  });

  const { data: products } = useQuery({
    queryKey: ['vendor-products', vendorId],
    queryFn: async () => {
      const response = await apiClient.getProducts({ vendor: vendorId });
      return response.data;
    },
  });

  if (vendorLoading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse space-y-8">
          <div className="h-48 rounded-lg bg-muted" />
          <div className="h-64 rounded-lg bg-muted" />
        </div>
      </div>
    );
  }

  if (!vendor) {
    return (
      <div className="container py-8">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Vendor not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const reviewsList = Array.isArray(reviews) ? reviews : reviews?.results || [];
  const productsList = Array.isArray(products) ? products : products?.results || [];

  return (
    <div className="container py-8">
      {/* Back Button */}
      <Link href="/" className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Back to products
      </Link>

      {/* Vendor Header */}
      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-6 md:flex-row">
            {vendor.logo ? (
              <img
                src={vendor.logo}
                alt={vendor.store_name}
                className="h-32 w-32 rounded-lg object-cover"
              />
            ) : (
              <div className="flex h-32 w-32 items-center justify-center rounded-lg bg-muted">
                <Store className="h-16 w-16 text-muted-foreground" />
              </div>
            )}

            <div className="flex-1 space-y-4">
              <div>
                <h1 className="text-3xl font-bold">{vendor.store_name}</h1>
                {vendor.description && (
                  <p className="mt-2 text-muted-foreground">{vendor.description}</p>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-6">
                <div className="flex items-center gap-2">
                  <StarRating rating={vendor.average_rating || 0} showValue />
                  <span className="text-sm text-muted-foreground">
                    ({vendor.total_reviews || 0} {vendor.total_reviews === 1 ? 'review' : 'reviews'})
                  </span>
                </div>

                {vendor.address && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    {vendor.address}
                  </div>
                )}

                {productsList.length > 0 && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Package className="h-4 w-4" />
                    {productsList.length} {productsList.length === 1 ? 'product' : 'products'}
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Reviews Section */}
        <div className="lg:col-span-2">
          <h2 className="mb-6 text-2xl font-bold">Customer Reviews</h2>
          
          {reviewsLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : reviewsList.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No reviews yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {reviewsList.map((review: any) => (
                <Card key={review.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                            {review.customer?.username?.[0]?.toUpperCase() || 'A'}
                          </div>
                          <div>
                            <p className="font-semibold">
                              {review.customer?.username || 'Anonymous'}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {format(new Date(review.created_at), 'MMM d, yyyy')}
                            </p>
                          </div>
                        </div>
                        <p className="text-sm leading-relaxed text-muted-foreground">
                          {review.review_text}
                        </p>
                      </div>
                      <StarRating rating={review.rating} />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Products Section */}
        <div>
          <h3 className="mb-4 text-xl font-bold">Products from this Vendor</h3>
          {productsList.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-sm text-muted-foreground">No products available</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {productsList.slice(0, 5).map((product: any) => (
                <Link
                  key={product.id}
                  href={`/products/${product.id}`}
                  className="block"
                >
                  <Card className="transition-shadow hover:shadow-md">
                    <CardContent className="flex gap-4 p-4">
                      {product.images?.[0] ? (
                        <img
                          src={product.images[0].image}
                          alt={product.name}
                          className="h-20 w-20 rounded-lg object-cover"
                        />
                      ) : (
                        <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-muted">
                          <Package className="h-8 w-8 text-muted-foreground" />
                        </div>
                      )}
                      <div className="flex-1 space-y-1">
                        <h4 className="font-semibold line-clamp-2">{product.name}</h4>
                        <p className="text-lg font-bold text-cyan-600">
                          ${parseFloat(product.price).toFixed(2)}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
              {productsList.length > 5 && (
                <Button variant="outline" className="w-full" asChild>
                  <Link href={`/products?vendor=${vendorId}`}>
                    View all {productsList.length} products
                  </Link>
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

