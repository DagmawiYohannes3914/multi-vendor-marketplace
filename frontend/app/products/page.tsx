'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, SlidersHorizontal, ShoppingBag } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { useCartStore } from '@/store/cart-store';
import { toast } from 'sonner';

export default function ProductsPage() {
  const searchParams = useSearchParams();
  const categoryId = searchParams.get('category');
  const [searchQuery, setSearchQuery] = useState('');
  const addToCart = useCartStore((state) => state.addItem);

  const { data: products, isLoading } = useQuery({
    queryKey: ['products', categoryId, searchQuery],
    queryFn: async () => {
      const params: any = {};
      if (categoryId) params.category = categoryId;
      if (searchQuery) params.search = searchQuery;
      
      const response = await apiClient.getProducts(params);
      return response.data;
    },
  });

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await apiClient.getCategories();
      return response.data;
    },
  });

  const handleAddToCart = (product: any) => {
    if (product.skus && product.skus.length > 0) {
      addToCart({
        id: product.skus[0].id,
        sku: product.skus[0].id,
        product: {
          id: product.id,
          name: product.name,
          price: product.price,
          images: product.images || [],
        },
        quantity: 1,
        unit_price: product.price,
      });
      toast.success('Added to cart!');
    } else {
      toast.error('Product unavailable');
    }
  };

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Products</h1>
        <p className="mt-2 text-muted-foreground">
          Browse our wide selection of products
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-8 flex flex-col gap-4 md:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 w-full rounded-md border border-input bg-background pl-10 pr-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>
        <Button variant="outline">
          <SlidersHorizontal className="mr-2 h-4 w-4" />
          Filters
        </Button>
      </div>

      {/* Category Filter */}
      {categories && categories.length > 0 && (
        <div className="mb-8">
          <div className="flex gap-2 overflow-x-auto pb-2">
            <Link href="/products">
              <Button
                variant={!categoryId ? 'default' : 'outline'}
                size="sm"
              >
                All
              </Button>
            </Link>
            {categories.map((category: any) => (
              <Link key={category.id} href={`/products?category=${category.id}`}>
                <Button
                  variant={categoryId === category.id ? 'default' : 'outline'}
                  size="sm"
                >
                  {category.name}
                </Button>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Products Grid */}
      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <div className="aspect-square bg-muted" />
              <CardHeader>
                <div className="h-4 w-3/4 rounded bg-muted" />
              </CardHeader>
              <CardContent>
                <div className="h-6 w-1/2 rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : products && products.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((product: any) => (
            <Card key={product.id} className="group overflow-hidden transition-shadow hover:shadow-lg">
              <Link href={`/products/${product.id}`}>
                <div className="aspect-square relative overflow-hidden bg-muted">
                  {product.images && product.images.length > 0 ? (
                    <Image
                      src={product.images[0].image}
                      alt={product.name}
                      fill
                      className="object-cover transition-transform group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <ShoppingBag className="h-12 w-12 text-muted-foreground" />
                    </div>
                  )}
                </div>
              </Link>
              <CardHeader>
                <Link href={`/products/${product.id}`}>
                  <CardTitle className="line-clamp-2 text-base transition-colors hover:text-primary">
                    {product.name}
                  </CardTitle>
                </Link>
                <p className="text-sm text-muted-foreground">
                  by {product.vendor?.store_name || 'Vendor'}
                </p>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold">
                    {formatPrice(product.price)}
                  </span>
                  {product.compare_price && (
                    <span className="text-sm text-muted-foreground line-through">
                      {formatPrice(product.compare_price)}
                    </span>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button
                  className="flex-1"
                  onClick={() => handleAddToCart(product)}
                >
                  Add to Cart
                </Button>
                <Button variant="outline" size="icon" asChild>
                  <Link href={`/products/${product.id}`}>
                    <ShoppingBag className="h-4 w-4" />
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20">
          <ShoppingBag className="h-16 w-16 text-muted-foreground" />
          <h2 className="mt-4 text-2xl font-semibold">No products found</h2>
          <p className="mt-2 text-muted-foreground">
            Try adjusting your search or filters
          </p>
        </div>
      )}
    </div>
  );
}

