# 🚀 Multi-Vendor Marketplace Frontend

A modern, responsive, and feature-rich e-commerce frontend built with Next.js 14, TypeScript, and Tailwind CSS.

## ✨ Features Implemented

### Core Infrastructure ✅
- ✅ Next.js 14 with App Router
- ✅ TypeScript for type safety
- ✅ Tailwind CSS + Shadcn/UI components
- ✅ React Query for data fetching & caching
- ✅ Zustand for state management
- ✅ Dark mode support
- ✅ Framer Motion for animations
- ✅ Responsive design (mobile-first)

### Pages & Features ✅
- ✅ **Landing Page** with hero, categories, featured products
- ✅ **Navbar** with cart, notifications, user menu, theme toggle
- ✅ **Footer** with links
- ✅ **API Client** with all backend endpoints integrated
- ✅ **Auth Store** for user management
- ✅ **Cart Store** for shopping cart

### Ready to Build 🚧
The following pages need to be created using the patterns established:

1. **Authentication Pages** (`/auth/login`, `/auth/register`)
2. **Product Pages** (`/products`, `/products/[id]`)
3. **Cart & Checkout** (`/cart`, `/checkout`)
4. **Account Pages** (`/account/orders`, `/account/profile`, `/account/addresses`)
5. **Vendor Dashboard** (`/vendor/dashboard`)
6. **Notifications** (`/notifications`)

---

## 🏗️ Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Landing page
│   ├── globals.css        # Global styles
│   ├── auth/              # Auth pages
│   ├── products/          # Product pages
│   ├── cart/              # Cart page
│   ├── checkout/          # Checkout page
│   ├── account/           # Customer account pages
│   ├── vendor/            # Vendor dashboard
│   └── notifications/     # Notifications page
├── components/            # Reusable components
│   ├── ui/               # UI components (Button, Card, etc.)
│   ├── navbar.tsx        # Navigation bar
│   ├── footer.tsx        # Footer
│   └── providers.tsx     # App providers
├── lib/                   # Utilities
│   ├── api-client.ts     # API client with all endpoints
│   └── utils.ts          # Utility functions
├── store/                 # State management
│   ├── auth-store.ts     # Authentication state
│   └── cart-store.ts     # Shopping cart state
└── types/                 # TypeScript types
```

---

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ and npm/yarn
- Backend server running at `http://localhost:8000`

### Installation

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Create environment file:**
Create a `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_key_here
```

3. **Run development server:**
```bash
npm run dev
```

4. **Open browser:**
Navigate to `http://localhost:3000`

---

## 📚 API Client Usage

The API client is fully configured with all backend endpoints. Use it in your components:

```typescript
import { apiClient } from '@/lib/api-client';

// Get products
const { data } = await apiClient.getProducts();

// Add to cart
await apiClient.addToCart(skuId, quantity);

// Checkout
await apiClient.checkout(checkoutData);
```

All endpoints from the backend are available. See `lib/api-client.ts` for the complete list.

---

## 🔐 Authentication Flow

The auth store handles all authentication:

```typescript
import { useAuthStore } from '@/store/auth-store';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuthStore();

  const handleLogin = async () => {
    await login(username, password);
    // User is now logged in
  };

  return (
    <div>
      {isAuthenticated ? (
        <p>Welcome {user?.username}</p>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
    </div>
  );
}
```

---

## 🛒 Shopping Cart

The cart store manages cart state:

```typescript
import { useCartStore } from '@/store/cart-store';

function CartButton() {
  const { items, addItem, getCartTotal, getItemCount } = useCartStore();
  const total = getCartTotal();
  const count = getItemCount();

  return (
    <button>
      Cart ({count}) - ${total.toFixed(2)}
    </button>
  );
}
```

---

## 🎨 Creating New Pages

### Example: Products List Page

Create `app/products/page.tsx`:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card } from '@/components/ui/card';

export default function ProductsPage() {
  const { data: products, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      const response = await apiClient.getProducts();
      return response.data;
    },
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold">Products</h1>
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {products.map((product: any) => (
          <Card key={product.id}>
            {/* Product card content */}
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### Example: Product Detail Page

Create `app/products/[id]/page.tsx`:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useCartStore } from '@/store/cart-store';

export default function ProductPage({ params }: { params: { id: string } }) {
  const { data: product } = useQuery({
    queryKey: ['product', params.id],
    queryFn: async () => {
      const response = await apiClient.getProduct(params.id);
      return response.data;
    },
  });

  const addToCart = useCartStore((state) => state.addItem);

  const handleAddToCart = () => {
    // Add product to cart
  };

  return (
    <div className="container py-8">
      <h1>{product?.name}</h1>
      {/* Product details */}
    </div>
  );
}
```

---

## 🎯 Key Pages to Build

### 1. Authentication Pages

**`app/auth/login/page.tsx`**
- Login form with username/password
- Call `useAuthStore().login()`
- Redirect to home or previous page

**`app/auth/register/page.tsx`**
- Registration form
- Support customer and vendor registration
- Call `useAuthStore().register()`

### 2. Product Pages

**`app/products/page.tsx`**
- Product listing with filters
- Search functionality
- Category filtering
- Pagination
- Use `apiClient.getProducts(params)`

**`app/products/[id]/page.tsx`**
- Product details
- Image gallery
- Add to cart
- Reviews section
- Q&A section
- Use `apiClient.getProduct(id)`

### 3. Cart & Checkout

**`app/cart/page.tsx`**
- Cart items list
- Update quantities
- Remove items
- Show total
- Proceed to checkout button

**`app/checkout/page.tsx`**
- Shipping address selection
- Payment method
- Order summary
- Stripe integration
- Use `apiClient.checkout(data)`

### 4. Account Pages

**`app/account/orders/page.tsx`**
- List user's orders
- Order status
- Track orders
- View receipts
- Request returns

**`app/account/profile/page.tsx`**
- User profile information
- Edit profile
- Change password

**`app/account/addresses/page.tsx`**
- Manage shipping addresses
- Add/edit/delete addresses
- Set default address

**`app/account/wishlist/page.tsx`**
- Wishlist items
- Add to cart from wishlist

### 5. Vendor Dashboard

**`app/vendor/dashboard/page.tsx`**
- Sales statistics
- Revenue charts
- Quick stats cards

**`app/vendor/orders/page.tsx`**
- Vendor orders list
- Update order status
- Add tracking numbers

**`app/vendor/products/page.tsx`**
- Product management
- Add/edit products
- Low stock alerts

**`app/vendor/analytics/page.tsx`**
- Product performance
- Revenue reports
- Customer insights

### 6. Additional Features

**`app/flash-sales/page.tsx`**
- Live flash sales
- Countdown timers
- Discounted prices

**`app/notifications/page.tsx`**
- Notifications list
- Mark as read
- Filter by type

---

## 🎨 UI Components

Use Shadcn/UI components for consistent design:

```typescript
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
```

### Creating More UI Components

To add more Shadcn/UI components:

1. Visit [ui.shadcn.com](https://ui.shadcn.com)
2. Browse components
3. Copy component code to `components/ui/`
4. Install required dependencies

Common components to add:
- Input, Label, Textarea (forms)
- Dialog, Sheet (modals)
- Select, Checkbox, RadioGroup (form inputs)
- Table (data display)
- Badge, Avatar (UI elements)
- Tabs, Accordion (layouts)

---

## 🎯 Features to Implement

### High Priority
- [ ] Login & Register pages
- [ ] Products listing page
- [ ] Product detail page
- [ ] Shopping cart page
- [ ] Checkout flow
- [ ] Order history
- [ ] Basic vendor dashboard

### Medium Priority
- [ ] Product search & filters
- [ ] Reviews & ratings
- [ ] Product Q&A
- [ ] Wishlist
- [ ] Address management
- [ ] Order tracking
- [ ] Return requests

### Nice to Have
- [ ] Flash sales page
- [ ] Vendor analytics
- [ ] Loyalty points display
- [ ] Referral program
- [ ] Product comparison
- [ ] Recently viewed

---

## 📱 Responsive Design

All components use Tailwind's responsive classes:

```typescript
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
  {/* Responsive grid */}
</div>
```

- **Mobile**: `grid-cols-1`
- **Tablet**: `sm:grid-cols-2`
- **Desktop**: `lg:grid-cols-4`

---

## 🌙 Dark Mode

Dark mode is already configured. Toggle with the button in navbar.

To use theme in components:

```typescript
import { useTheme } from 'next-themes';

function MyComponent() {
  const { theme, setTheme } = useTheme();
  // theme is 'light' or 'dark'
}
```

---

## 🔄 Data Fetching Pattern

Use React Query for all API calls:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch data
const { data, isLoading, error } = useQuery({
  queryKey: ['products'],
  queryFn: async () => {
    const response = await apiClient.getProducts();
    return response.data;
  },
});

// Mutate data
const queryClient = useQueryClient();
const mutation = useMutation({
  mutationFn: (data) => apiClient.createProduct(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['products'] });
  },
});
```

---

## 🎬 Animations

Use Framer Motion for animations:

```typescript
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6 }}
>
  {/* Content */}
</motion.div>
```

---

## 🐛 Error Handling

Handle errors gracefully:

```typescript
try {
  await apiClient.login(username, password);
} catch (error) {
  toast.error('Login failed. Please check your credentials.');
}
```

Use `sonner` for toast notifications:

```typescript
import { toast } from 'sonner';

toast.success('Product added to cart!');
toast.error('Something went wrong');
toast.loading('Processing...');
```

---

## 🔒 Protected Routes

Create a middleware or HOC for protected pages:

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token');
  
  if (!token && request.nextUrl.pathname.startsWith('/account')) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/account/:path*', '/vendor/:path*'],
};
```

---

## 📦 Additional Libraries to Consider

- **Form Management**: `react-hook-form` with `zod` validation
- **Date Formatting**: `date-fns`
- **Charts**: `recharts` (for vendor analytics)
- **Image Upload**: `react-dropzone`
- **Rich Text**: `@tiptap/react` (for product descriptions)

---

## 🚀 Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy

### Build for Production

```bash
npm run build
npm start
```

---

## 📝 Code Quality

### Linting
```bash
npm run lint
```

### Formatting
Use Prettier:
```bash
npm install -D prettier
npm run format
```

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

---

## 📞 Support

For backend API documentation, see:
- `backend/API_ENDPOINTS_FOR_FRONTEND.md`
- `backend/SYSTEM_ARCHITECTURE.md`

---

## ✅ Next Steps

1. **Install dependencies**: `npm install`
2. **Run dev server**: `npm run dev`
3. **Start building pages** using the patterns shown
4. **Test with backend** running at `localhost:8000`
5. **Deploy** when ready

---

**Happy Coding! 🎉**

The foundation is solid. Build amazing features on top of it!

