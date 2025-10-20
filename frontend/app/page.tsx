'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import Image from 'next/image';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ArrowRight, ShoppingCart, Heart, Star } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/auth-store';
import { useCartStore } from '@/store/cart-store';

export default function Home() {
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const { data: products } = useQuery({
    queryKey: ['featured-products'],
    queryFn: async () => {
      const response = await apiClient.getProducts({ limit: 8 });
      return response.data;
    },
  });

  const addToCartMutation = useMutation({
    mutationFn: ({ sku, quantity }: { sku: string; quantity: number }) =>
      apiClient.addToCart(sku, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      toast.success('Added to cart!');
    },
    onError: () => {
      toast.error('Failed to add to cart');
    },
  });

  const addToWishlistMutation = useMutation({
    mutationFn: (sku: string) => apiClient.addToWishlist(sku),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
      toast.success('Added to wishlist!');
    },
    onError: () => {
      toast.error('Failed to add to wishlist');
    },
  });

  const addGuestItem = useCartStore((state) => state.addGuestItem);

  const handleAddToCart = (e: React.MouseEvent, product: any) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (product.skus && product.skus.length > 0) {
      const sku = product.skus[0].sku_code;
      
      if (isAuthenticated) {
        // Add to backend cart
        addToCartMutation.mutate({ sku, quantity: 1 });
      } else {
        // Add to guest cart (localStorage)
        addGuestItem({
          sku,
          sku_id: product.skus[0].id,  // SKU UUID for backend API
          product_id: product.id,
          product_name: product.name,
          product_price: product.price,
          product_image: product.images?.[0]?.image,
          vendor_name: product.vendor?.business_name,
          quantity: 1,
        });
        toast.success('Added to cart!');
      }
    }
  };

  const handleAddToWishlist = (e: React.MouseEvent, product: any) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      toast.error('Please login to add items to wishlist');
      return;
    }
    if (product.skus && product.skus.length > 0) {
      addToWishlistMutation.mutate(product.skus[0].sku_code);
    }
  };

  const calculateDiscount = (price: number, comparePrice: number) => {
    if (!comparePrice || comparePrice <= price) return null;
    return Math.round(((comparePrice - price) / comparePrice) * 100);
  };

  // Newsletter subscription
  const [email, setEmail] = useState('');
  const [newsletterSubmitted, setNewsletterSubmitted] = useState(false);

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      // For now, just show success (backend integration later)
      setNewsletterSubmitted(true);
      toast.success('Thank you for subscribing to our newsletter!');
      setEmail('');
      setTimeout(() => setNewsletterSubmitted(false), 3000);
    }
  };

  // Get product badges
  const getBadge = (product: any) => {
    const badges = [];
    
    // New badge (created within last 7 days)
    const createdDate = new Date(product.created_at);
    const daysSinceCreation = (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24);
    if (daysSinceCreation < 7) {
      badges.push({ text: 'NEW', color: 'bg-blue-500' });
    }
    
    // Sale badge (has discount)
    const discount = product.compare_price
      ? calculateDiscount(product.price, product.compare_price)
      : null;
    if (discount && discount > 0) {
      badges.push({ text: 'SALE', color: 'bg-red-500' });
    }
    
    // Best Seller badge (high sales or ratings)
    if (product.average_rating >= 4.5 || product.sold_count > 100) {
      badges.push({ text: 'BEST SELLER', color: 'bg-green-500' });
    }
    
    return badges;
  };

  return (
    <div className="flex flex-col">
      {/* Hero Section with Gradient */}
      <section className="relative overflow-hidden bg-gradient-to-br from-cyan-500 via-blue-500 to-purple-600 py-20 text-white md:py-32">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="container relative z-10">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-8 text-center lg:text-left"
            >
              <div className="inline-block rounded-full bg-white/20 px-4 py-2 text-sm font-semibold backdrop-blur-sm">
                ⚡ Limited Time Offer - Up to 50% OFF
              </div>
              <h1 className="text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl">
                Discover Amazing Products from Trusted Vendors
              </h1>
              <p className="text-lg text-white/90 sm:text-xl">
                Shop from thousands of products across multiple categories. Quality guaranteed, competitive prices, and secure transactions.
              </p>
              <div className="flex flex-col gap-4 sm:flex-row lg:justify-start">
                <Button size="lg" asChild className="bg-white text-cyan-600 hover:bg-gray-100">
                  <Link href="/products">
                    Start Shopping <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="border-white bg-white/10 text-white backdrop-blur-sm hover:bg-white/20">
                  <Link href="/auth/register?vendor=true">
                    Become a Vendor
                  </Link>
                </Button>
              </div>
              
              {/* Trust Indicators */}
              <div className="flex flex-wrap items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="rounded-full bg-white/20 p-2">
                    <ShoppingCart className="h-4 w-4" />
                  </div>
                  <span>1000+ Products</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="rounded-full bg-white/20 p-2">
                    <Star className="h-4 w-4" />
                  </div>
                  <span>4.8 Average Rating</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="rounded-full bg-white/20 p-2">
                    <Heart className="h-4 w-4" />
                  </div>
                  <span>50k+ Happy Customers</span>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative hidden lg:block"
            >
              <div className="relative aspect-square">
                <div className="absolute inset-0 rounded-full bg-white/10 backdrop-blur-sm"></div>
                <div className="absolute inset-8 rounded-full bg-white/10 backdrop-blur-sm"></div>
                <div className="absolute inset-16 rounded-full bg-white/10 backdrop-blur-sm"></div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Featured Products with Badges */}
      <section className="py-16">
        <div className="container">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold lg:text-4xl">Featured Products</h2>
            <p className="mt-2 text-muted-foreground">Handpicked products just for you</p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {products?.slice(0, 8).map((product: any) => {
              const discount = product.compare_price
                ? calculateDiscount(product.price, product.compare_price)
                : null;
              const rating = product.average_rating || 4.7;
              const reviewCount = product.review_count || 128;
              const badges = getBadge(product);

              return (
                <Link key={product.id} href={`/products/${product.id}`}>
                  <Card className="group relative overflow-hidden transition-all hover:shadow-xl">
                    <div className="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-800">
                      {product.images && product.images.length > 0 ? (
                        <Image
                          src={product.images[0].image}
                          alt={product.name}
                          fill
                          className="object-cover transition-transform duration-300 group-hover:scale-110"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center">
                          <ShoppingCart className="h-16 w-16 text-muted-foreground" />
                        </div>
                      )}
                      
                      {/* Multiple Badges */}
                      <div className="absolute left-3 top-3 flex flex-col gap-2">
                        {badges.map((badge, index) => (
                          <div
                            key={index}
                            className={`${badge.color} rounded-full px-2 py-1 text-xs font-bold text-white shadow-lg`}
                          >
                            {badge.text}
                          </div>
                        ))}
                        {discount && discount > 0 && (
                          <div className="rounded-full bg-orange-500 px-2 py-1 text-xs font-bold text-white shadow-lg">
                            {discount}% OFF
                          </div>
                        )}
                      </div>

                      <button
                        onClick={(e) => handleAddToWishlist(e, product)}
                        className="absolute right-3 top-3 rounded-full bg-white p-2 shadow-lg transition-transform hover:scale-110 dark:bg-gray-800"
                      >
                        <Heart className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                      </button>
                    </div>

                    <div className="space-y-3 p-4">
                      <div>
                        <h3 className="font-semibold line-clamp-2 text-base">
                          {product.name}
                        </h3>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {product.vendor?.business_name || 'Vendor Store'}
                        </p>
                      </div>

                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 fill-orange-400 text-orange-400" />
                        <span className="text-sm font-medium">{rating.toFixed(1)}</span>
                        <span className="text-sm text-muted-foreground">({reviewCount})</span>
                      </div>

                      <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-cyan-600 dark:text-cyan-400">
                          {formatPrice(product.price)}
                        </span>
                        {product.compare_price && product.compare_price > product.price && (
                          <span className="text-sm text-muted-foreground line-through">
                            {formatPrice(product.compare_price)}
                          </span>
                        )}
                      </div>

                      <Button
                        onClick={(e) => handleAddToCart(e, product)}
                        className="w-full bg-cyan-600 hover:bg-cyan-700"
                        disabled={addToCartMutation.isPending}
                      >
                        <ShoppingCart className="mr-2 h-4 w-4" />
                        Add to Cart
                      </Button>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>

          <div className="mt-12 text-center">
            <Button size="lg" variant="outline" asChild>
              <Link href="/products">
                View All Products <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="bg-gradient-to-r from-cyan-600 to-blue-600 py-16 text-white">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">Join Our Newsletter</h2>
            <p className="mt-4 text-lg text-white/90">
              Get exclusive deals, new product alerts, and special offers delivered to your inbox!
            </p>
            
            {!newsletterSubmitted ? (
              <form onSubmit={handleNewsletterSubmit} className="mt-8 flex flex-col gap-3 sm:flex-row">
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="flex-1 rounded-lg border-0 px-4 py-3 text-gray-900 placeholder:text-gray-500 focus:ring-2 focus:ring-white"
                />
                <Button type="submit" size="lg" className="bg-white text-cyan-600 hover:bg-gray-100">
                  Subscribe
                </Button>
              </form>
            ) : (
              <div className="mt-8 rounded-lg bg-white/20 p-4 backdrop-blur-sm">
                <p className="text-lg font-semibold">✓ You're subscribed! Check your email for confirmation.</p>
              </div>
            )}
            
            <p className="mt-4 text-sm text-white/70">
              We respect your privacy. Unsubscribe anytime.
            </p>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="border-t py-12">
        <div className="container">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-cyan-100 dark:bg-cyan-900">
                <ShoppingCart className="h-8 w-8 text-cyan-600 dark:text-cyan-400" />
              </div>
              <h3 className="mt-4 font-semibold">Free Shipping</h3>
              <p className="mt-2 text-sm text-muted-foreground">On orders over $50</p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                <Star className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="mt-4 font-semibold">Quality Products</h3>
              <p className="mt-2 text-sm text-muted-foreground">Verified vendors only</p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-orange-100 dark:bg-orange-900">
                <Heart className="h-8 w-8 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="mt-4 font-semibold">30-Day Returns</h3>
              <p className="mt-2 text-sm text-muted-foreground">Easy return policy</p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900">
                <ArrowRight className="h-8 w-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="mt-4 font-semibold">Secure Payments</h3>
              <p className="mt-2 text-sm text-muted-foreground">100% protected</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

