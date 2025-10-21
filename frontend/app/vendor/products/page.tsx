'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Edit, Eye, AlertTriangle, ArrowLeft, Package } from 'lucide-react';
import { formatPrice } from '@/lib/utils';

export default function VendorProductsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const { data: products, isLoading } = useQuery({
    queryKey: ['vendor-products'],
    queryFn: async () => {
      // Get all products filtered by current vendor
      const response = await apiClient.getProducts({ vendor: user?.vendor_profile?.id });
      return response.data;
    },
    enabled: isAuthenticated && user?.is_vendor,
  });

  const { data: lowStockAlerts } = useQuery({
    queryKey: ['low-stock-alerts'],
    queryFn: async () => {
      const response = await apiClient.getLowStockAlerts();
      return response.data;
    },
    enabled: isAuthenticated && user?.is_vendor,
  });

  if (!isAuthenticated || !user?.is_vendor) {
    router.push('/auth/login');
    return null;
  }

  const productsList = Array.isArray(products) ? products : products?.results || [];
  const lowStockList = Array.isArray(lowStockAlerts) ? lowStockAlerts : lowStockAlerts?.results || [];

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

      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Products</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your product inventory
          </p>
        </div>
        <Button asChild>
          <Link href="/vendor/products/new">
            <Plus className="mr-2 h-4 w-4" />
            Add New Product
          </Link>
        </Button>
      </div>

      {/* Low Stock Alerts */}
      {lowStockList.length > 0 && (
        <Card className="mb-6 border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-900/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-900 dark:text-orange-100">
              <AlertTriangle className="h-5 w-5" />
              Low Stock Alerts ({lowStockList.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {lowStockList.slice(0, 5).map((alert: any) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between rounded-lg border border-orange-200 bg-white p-3 dark:border-orange-800 dark:bg-orange-950/50"
                >
                  <div>
                    <p className="font-medium">{alert.product?.name || 'Product'}</p>
                    <p className="text-sm text-muted-foreground">
                      SKU: {alert.sku?.sku_code}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-orange-600">
                      {alert.sku?.stock_quantity} left
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Threshold: {alert.threshold}
                    </p>
                  </div>
                </div>
              ))}
              {lowStockList.length > 5 && (
                <p className="text-sm text-muted-foreground">
                  +{lowStockList.length - 5} more items with low stock
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Products List */}
      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-96 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : productsList.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Package className="h-16 w-16 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">No Products Yet</h2>
            <p className="mt-2 text-center text-muted-foreground">
              Start by adding your first product
            </p>
            <Button className="mt-6" asChild>
              <Link href="/vendor/products/new">
                <Plus className="mr-2 h-4 w-4" />
                Add Product
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {productsList.map((product: any) => {
            const totalStock = product.skus?.reduce(
              (sum: number, sku: any) => sum + (sku.stock_quantity || 0),
              0
            );
            const isLowStock = lowStockList.some((alert: any) =>
              product.skus?.some((sku: any) => sku.id === alert.sku?.id)
            );

            return (
              <Card key={product.id} className="overflow-hidden">
                {isLowStock && (
                  <div className="bg-orange-100 px-3 py-1 text-center text-xs font-medium text-orange-900 dark:bg-orange-900 dark:text-orange-100">
                    Low Stock Alert
                  </div>
                )}
                <div className="relative aspect-square overflow-hidden bg-muted">
                  {product.images?.[0] ? (
                    <Image
                      src={product.images[0].image}
                      alt={product.name}
                      fill
                      className="object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <Package className="h-16 w-16 text-muted-foreground" />
                    </div>
                  )}
                </div>
                <CardContent className="p-4">
                  <h3 className="font-semibold line-clamp-2">{product.name}</h3>

                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-lg font-bold text-cyan-600">
                      {formatPrice(product.price)}
                    </span>
                    {product.compare_price && product.compare_price > product.price && (
                      <span className="text-sm text-muted-foreground line-through">
                        {formatPrice(product.compare_price)}
                      </span>
                    )}
                  </div>

                  <div className="mt-2 flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Stock:</span>
                    <span
                      className={`font-medium ${
                        totalStock === 0
                          ? 'text-red-600'
                          : isLowStock
                          ? 'text-orange-600'
                          : 'text-green-600'
                      }`}
                    >
                      {totalStock} units
                    </span>
                  </div>

                  {product.is_active ? (
                    <div className="mt-2 text-sm">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
                        Active
                      </span>
                    </div>
                  ) : (
                    <div className="mt-2 text-sm">
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800 dark:bg-gray-900 dark:text-gray-200">
                        Inactive
                      </span>
                    </div>
                  )}

                  <div className="mt-4 flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1" asChild>
                      <Link href={`/products/${product.id}`}>
                        <Eye className="mr-2 h-4 w-4" />
                        View
                      </Link>
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1" asChild>
                      <Link href={`/vendor/products/${product.id}/edit`}>
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Quick Stats */}
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold">{productsList.length}</p>
              <p className="text-sm text-muted-foreground">Total Products</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold">
                {productsList.filter((p: any) => p.is_active).length}
              </p>
              <p className="text-sm text-muted-foreground">Active Products</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-orange-600">{lowStockList.length}</p>
              <p className="text-sm text-muted-foreground">Low Stock Alerts</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

