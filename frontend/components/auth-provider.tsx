'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth-store';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const fetchUser = useAuthStore((state) => state.fetchUser);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    // Check if there's a token in localStorage
    const token = localStorage.getItem('access_token');
    
    // If there's a token but we're not authenticated, fetch user
    if (token && !isAuthenticated) {
      fetchUser().catch(() => {
        // If fetch fails, token is invalid - do nothing, user will need to login
        console.log('Token invalid or expired');
      });
    }
  }, []);

  return <>{children}</>;
}

