import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface GuestCartItem {
  sku: string; // SKU code for display
  sku_id: string; // SKU UUID for backend API
  product_id: string;
  product_name: string;
  product_price: string;
  product_image?: string;
  quantity: number;
  vendor_name?: string;
}

interface CartState {
  guestItems: GuestCartItem[];
  addGuestItem: (item: GuestCartItem) => void;
  removeGuestItem: (sku: string) => void;
  updateGuestItemQuantity: (sku: string, quantity: number) => void;
  clearGuestCart: () => void;
  getGuestCartTotal: () => number;
  getGuestItemCount: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      guestItems: [],

      addGuestItem: (item) => {
        set((state) => {
          const existingItem = state.guestItems.find((i) => i.sku === item.sku);
          if (existingItem) {
            return {
              guestItems: state.guestItems.map((i) =>
                i.sku === item.sku
                  ? { ...i, quantity: i.quantity + item.quantity }
                  : i
              ),
            };
          }
          return { guestItems: [...state.guestItems, item] };
        });
      },

      removeGuestItem: (sku) => {
        set((state) => ({
          guestItems: state.guestItems.filter((i) => i.sku !== sku),
        }));
      },

      updateGuestItemQuantity: (sku, quantity) => {
        set((state) => ({
          guestItems: state.guestItems.map((i) =>
            i.sku === sku ? { ...i, quantity } : i
          ),
        }));
      },

      clearGuestCart: () => {
        set({ guestItems: [] });
      },

      getGuestCartTotal: () => {
        return get().guestItems.reduce((total, item) => {
          return total + parseFloat(item.product_price) * item.quantity;
        }, 0);
      },

      getGuestItemCount: () => {
        return get().guestItems.reduce((count, item) => count + item.quantity, 0);
      },
    }),
    {
      name: 'guest-cart-storage',
    }
  )
);

