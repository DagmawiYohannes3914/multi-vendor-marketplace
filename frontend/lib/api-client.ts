import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const { data } = await axios.post(`${API_URL}/api/accounts/token/refresh/`, {
                refresh: refreshToken,
              });
              
              this.setToken(data.access);
              originalRequest.headers.Authorization = `Bearer ${data.access}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.clearTokens();
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/login';
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  private setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  private clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  // Auth endpoints
  async register(data: any) {
    return this.client.post('/accounts/register/', data);
  }

  async login(username: string, password: string) {
    const response = await this.client.post('/accounts/login/', { username, password });
    if (response.data.access && response.data.refresh) {
      this.setToken(response.data.access);
      if (typeof window !== 'undefined') {
        localStorage.setItem('refresh_token', response.data.refresh);
      }
    }
    return response;
  }

  async logout() {
    const refreshToken = this.getRefreshToken();
    if (refreshToken) {
      await this.client.post('/accounts/logout/', { refresh: refreshToken });
    }
    this.clearTokens();
  }

  async getProfile() {
    return this.client.get('/accounts/profile/');
  }

  // Products
  async getProducts(params?: any) {
    return this.client.get('/products/products/', { params });
  }

  async getProduct(id: string) {
    return this.client.get(`/products/products/${id}/`);
  }

  async getCategories() {
    return this.client.get('/products/categories/');
  }

  async getCategoryTree() {
    return this.client.get('/products/categories/tree/');
  }

  // Flash Sales
  async getLiveFlashSales() {
    return this.client.get('/products/flash-sales/live/');
  }

  async getFlashSalePrice(saleId: string, productId: string) {
    return this.client.get(`/products/flash-sales/${saleId}/get_discounted_price/`, {
      params: { product_id: productId }
    });
  }

  // Cart
  async getCart() {
    return this.client.get('/orders/cart/');
  }

  async addToCart(sku: string, quantity: number) {
    return this.client.post('/orders/cart/add_item/', { sku, quantity });
  }

  async updateCartItem(item_id: string, quantity: number) {
    return this.client.post('/orders/cart/update_item/', { item_id, quantity });
  }

  async removeFromCart(item_id: string) {
    return this.client.post('/orders/cart/remove_item/', { item_id });
  }

  async clearCart() {
    return this.client.post('/orders/cart/clear/');
  }

  // Checkout
  async checkout(data: any) {
    return this.client.post('/orders/checkout/', data);
  }

  async applyCoupon(code: string) {
    return this.client.post('/orders/coupons/validate/', { code });
  }

  // Orders
  async getOrders(params?: any) {
    return this.client.get('/orders/orders/', { params });
  }

  async getOrder(id: string) {
    return this.client.get(`/orders/orders/${id}/`);
  }

  async getOrderReceipt(id: string) {
    return this.client.get(`/orders/orders/${id}/receipt/`);
  }

  // Shipping Addresses
  async getShippingAddresses() {
    return this.client.get('/orders/shipping-addresses/');
  }

  async createShippingAddress(data: any) {
    return this.client.post('/orders/shipping-addresses/', data);
  }

  async updateShippingAddress(id: string, data: any) {
    return this.client.put(`/orders/shipping-addresses/${id}/`, data);
  }

  async deleteShippingAddress(id: string) {
    return this.client.delete(`/orders/shipping-addresses/${id}/`);
  }

  async setDefaultAddress(id: string) {
    return this.client.post(`/orders/shipping-addresses/${id}/set_default/`);
  }

  // Returns
  async createReturn(data: any) {
    return this.client.post('/orders/returns/', data);
  }

  async getReturns() {
    return this.client.get('/orders/returns/');
  }

  async getReturn(id: string) {
    return this.client.get(`/orders/returns/${id}/`);
  }

  async uploadReturnImage(returnId: string, image: File) {
    const formData = new FormData();
    formData.append('return', returnId);
    formData.append('image', image);
    return this.client.post('/orders/returns/upload_image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }

  // Cancellations
  async requestCancellation(orderId: string, data: any) {
    return this.client.post('/orders/cancellations/', {
      order: orderId,
      ...data
    });
  }

  async getCancellations() {
    return this.client.get('/orders/cancellations/');
  }

  async getCancellation(id: string) {
    return this.client.get(`/orders/cancellations/${id}/`);
  }

  async getOrderCancellation(orderId: string) {
    return this.client.get('/orders/cancellations/', { params: { order: orderId } });
  }

  // Shipping Rates
  async getShippingRates(params?: any) {
    return this.client.get('/orders/shipping-rates/', { params });
  }

  async calculateShipping(data: any) {
    return this.client.post('/orders/shipping-rates/calculate/', data);
  }

  // Reviews
  async createReview(data: any) {
    return this.client.post('/products/ratings/', data);
  }

  async getReviews(productId: string) {
    return this.client.get('/products/ratings/', { params: { product_id: productId } });
  }

  async voteReview(ratingId: string, voteType: 'helpful' | 'not_helpful') {
    return this.client.post(`/products/ratings/${ratingId}/vote/`, { vote_type: voteType });
  }

  async updateReview(id: string, data: any) {
    return this.client.put(`/products/ratings/${id}/`, data);
  }

  async deleteReview(id: string) {
    return this.client.delete(`/products/ratings/${id}/`);
  }

  async uploadReviewImage(reviewId: string, image: File) {
    const formData = new FormData();
    formData.append('review', reviewId);
    formData.append('image', image);
    return this.client.post('/products/ratings/upload_image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }

  async getReviewImages(reviewId: string) {
    return this.client.get('/products/ratings/images/', { params: { review_id: reviewId } });
  }

  // Q&A
  async askQuestion(data: any) {
    return this.client.post('/products/questions/', data);
  }

  async answerQuestion(data: any) {
    return this.client.post('/products/answers/', data);
  }

  async getProductQA(productId: string) {
    return this.client.get(`/products/products/${productId}/qa/`);
  }

  // Wishlist
  async getWishlist() {
    return this.client.get('/products/wishlists/');
  }

  async addToWishlist(productId: string, wishlistId?: string) {
    // If wishlistId is provided, add product to existing wishlist
    // Otherwise, create a new wishlist with the product
    if (wishlistId) {
      return this.client.post(`/products/wishlists/${wishlistId}/add_product/`, { product_id: productId });
    }
    return this.client.post('/products/wishlists/', { name: 'My Wishlist', products: [productId] });
  }

  async removeFromWishlist(wishlistId: string, productId: string) {
    return this.client.post(`/products/wishlists/${wishlistId}/remove_product/`, { product_id: productId });
  }

  // Loyalty Points
  async getLoyaltyBalance() {
    return this.client.get('/products/loyalty-points/balance/');
  }

  // Referrals
  async getMyReferralCode() {
    return this.client.get('/products/referrals/my_code/');
  }

  async applyReferralCode(code: string) {
    return this.client.post('/products/referrals/apply/', { code });
  }

  // Notifications
  async getNotifications(params?: any) {
    return this.client.get('/notifications/', { params });
  }

  async markNotificationAsRead(id: string) {
    return this.client.post(`/notifications/${id}/mark_as_read/`);
  }

  async markAllNotificationsAsRead() {
    return this.client.post('/notifications/mark_all_as_read/');
  }

  async deleteNotification(id: string) {
    return this.client.delete(`/notifications/${id}/`);
  }

  // Vendor Dashboard
  async getVendorStats() {
    return this.client.get('/profiles/vendor/dashboard/stats/');
  }

  async getVendorOrders(params?: any) {
    return this.client.get('/profiles/vendor/dashboard/orders/', { params });
  }

  async getVendorOrderDetail(orderId: string) {
    return this.client.get('/profiles/vendor/dashboard/order_detail/', { params: { order_id: orderId } });
  }

  async updateVendorOrder(data: any) {
    return this.client.post('/profiles/vendor/dashboard/update_order/', data);
  }

  async updateVendorOrderStatus(orderId: string, status: string) {
    return this.client.post('/profiles/vendor/dashboard/update_order/', { 
      order_id: orderId, 
      status 
    });
  }

  async getProductPerformance() {
    return this.client.get('/profiles/vendor/dashboard/product_performance/');
  }

  async getLowStockAlerts() {
    return this.client.get('/profiles/vendor/dashboard/low_stock_alerts/');
  }

  async getRevenueReport(params?: any) {
    return this.client.get('/profiles/vendor/dashboard/revenue_report/', { params });
  }

  async getVendorReturns(params?: any) {
    return this.client.get('/orders/returns/vendor_returns/', { params });
  }

  async approveReturn(id: string, notes: string) {
    return this.client.post(`/orders/returns/${id}/approve/`, { notes });
  }

  async rejectReturn(id: string, notes: string) {
    return this.client.post(`/orders/returns/${id}/reject/`, { notes });
  }

  // Vendor Reviews
  async getVendorProfile(vendorId: string) {
    return this.client.get(`/profiles/vendor/${vendorId}/`);
  }

  async createVendorReview(vendorId: string, data: any) {
    return this.client.post('/profiles/reviews/', { ...data, vendor: vendorId });
  }

  async getVendorReviews(vendorId: string, params?: any) {
    return this.client.get('/profiles/reviews/', { params: { vendor_id: vendorId, ...params } });
  }

  async updateVendorReview(id: string, data: any) {
    return this.client.put(`/profiles/reviews/${id}/`, data);
  }

  async deleteVendorReview(id: string) {
    return this.client.delete(`/profiles/reviews/${id}/`);
  }

  // Stripe
  async getStripeConfig() {
    return this.client.get('/orders/payments/stripe/config/');
  }
}

export const apiClient = new APIClient();

