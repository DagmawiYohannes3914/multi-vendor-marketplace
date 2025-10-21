'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ArrowLeft,
  TrendingUp,
  DollarSign,
  Package,
  Users,
  ShoppingCart,
  Star,
  BarChart3,
} from 'lucide-react';
import { formatPrice } from '@/lib/utils';

export default function VendorAnalyticsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const { data: stats, isLoading } = useQuery({
    queryKey: ['vendor-stats'],
    queryFn: async () => {
      const response = await apiClient.getVendorStats();
      return response.data;
    },
    enabled: isAuthenticated && user?.is_vendor,
  });

  if (!isAuthenticated || !user?.is_vendor) {
    router.push('/auth/login');
    return null;
  }

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
        <h1 className="text-3xl font-bold">Analytics & Reports</h1>
        <p className="mt-2 text-muted-foreground">
          Detailed insights into your store performance
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          {/* Key Metrics */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPrice(stats?.total_revenue || 0)}
                </div>
                <p className="text-xs text-muted-foreground">All time earnings</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
                <ShoppingCart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_orders || 0}</div>
                <p className="text-xs text-muted-foreground">Completed orders</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Products Sold</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.total_products_sold || 0}
                </div>
                <p className="text-xs text-muted-foreground">Units sold</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Average Rating</CardTitle>
                <Star className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.average_rating?.toFixed(1) || '0.0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  From {stats?.total_reviews || 0} reviews
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Revenue Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Revenue Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Pending Orders</span>
                  <span className="font-medium">
                    {formatPrice(stats?.pending_revenue || 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Processing Orders</span>
                  <span className="font-medium">
                    {formatPrice(stats?.processing_revenue || 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Completed Orders</span>
                  <span className="font-medium">
                    {formatPrice(stats?.completed_revenue || 0)}
                  </span>
                </div>
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Total Revenue</span>
                    <span className="text-lg font-bold text-cyan-600">
                      {formatPrice(stats?.total_revenue || 0)}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Order Status Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Order Status Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span>Pending</span>
                    <span className="font-medium">{stats?.pending_orders || 0}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full bg-yellow-500"
                      style={{
                        width: `${
                          ((stats?.pending_orders || 0) / (stats?.total_orders || 1)) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span>Processing</span>
                    <span className="font-medium">{stats?.processing_orders || 0}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full bg-blue-500"
                      style={{
                        width: `${
                          ((stats?.processing_orders || 0) / (stats?.total_orders || 1)) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span>Shipped</span>
                    <span className="font-medium">{stats?.shipped_orders || 0}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full bg-purple-500"
                      style={{
                        width: `${
                          ((stats?.shipped_orders || 0) / (stats?.total_orders || 1)) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span>Delivered</span>
                    <span className="font-medium">{stats?.delivered_orders || 0}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full bg-green-500"
                      style={{
                        width: `${
                          ((stats?.delivered_orders || 0) / (stats?.total_orders || 1)) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Customer Insights */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Customer Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <p className="text-2xl font-bold">{stats?.total_customers || 0}</p>
                  <p className="text-sm text-muted-foreground">Total Customers</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.repeat_customers || 0}</p>
                  <p className="text-sm text-muted-foreground">Repeat Customers</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {formatPrice(stats?.average_order_value || 0)}
                  </p>
                  <p className="text-sm text-muted-foreground">Avg Order Value</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

