'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { User, Mail, Badge as BadgeIcon, Star, TrendingUp, Gift, Copy, Share2 } from 'lucide-react';
import { toast } from 'sonner';

export default function ProfilePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
  });

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const response = await apiClient.getProfile();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  const { data: loyaltyPoints } = useQuery({
    queryKey: ['loyalty-points'],
    queryFn: async () => {
      const response = await apiClient.getMyLoyaltyPoints();
      return response.data;
    },
    enabled: isAuthenticated && user?.is_customer,
  });

  const { data: referralData } = useQuery({
    queryKey: ['referral-program'],
    queryFn: async () => {
      const response = await apiClient.getReferralProgram();
      return response.data;
    },
    enabled: isAuthenticated,
  });

  const handleCopyReferralCode = () => {
    if (referralData?.referral_code) {
      navigator.clipboard.writeText(referralData.referral_code);
      toast.success('Referral code copied to clipboard!');
    }
  };

  const handleShareReferral = () => {
    if (referralData?.referral_code) {
      const shareUrl = `${window.location.origin}/register?ref=${referralData.referral_code}`;
      if (navigator.share) {
        navigator.share({
          title: 'Join our marketplace!',
          text: `Use my referral code: ${referralData.referral_code}`,
          url: shareUrl,
        });
      } else {
        navigator.clipboard.writeText(shareUrl);
        toast.success('Referral link copied to clipboard!');
      }
    }
  };

  if (!isAuthenticated) {
    router.push('/auth/login');
    return null;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success('Profile updated!');
    setIsEditing(false);
  };

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">My Profile</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your account information
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Profile Info */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">First Name</label>
                      <input
                        type="text"
                        value={formData.first_name}
                        onChange={(e) =>
                          setFormData({ ...formData, first_name: e.target.value })
                        }
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Last Name</label>
                      <input
                        type="text"
                        value={formData.last_name}
                        onChange={(e) =>
                          setFormData({ ...formData, last_name: e.target.value })
                        }
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Email</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) =>
                        setFormData({ ...formData, email: e.target.value })
                      }
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit">Save Changes</Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsEditing(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <User className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Name</p>
                      <p className="font-medium">
                        {user?.first_name} {user?.last_name}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Email</p>
                      <p className="font-medium">{user?.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <BadgeIcon className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Username</p>
                      <p className="font-medium">{user?.username}</p>
                    </div>
                  </div>
                  <Button onClick={() => setIsEditing(true)}>Edit Profile</Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Account Stats */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {user?.is_customer && (
                  <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
                    <p className="text-sm font-medium text-green-900 dark:text-green-100">
                      Customer Account
                    </p>
                  </div>
                )}
                {user?.is_vendor && (
                  <div className="rounded-lg bg-purple-50 p-3 dark:bg-purple-900/20">
                    <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
                      Vendor Account
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Loyalty Points */}
          {user?.is_customer && loyaltyPoints && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="h-5 w-5 text-yellow-500" />
                  Loyalty Points
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <p className="text-4xl font-bold text-cyan-600">
                      {loyaltyPoints.total_points || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Available Points</p>
                  </div>
                  
                  {loyaltyPoints.points_used > 0 && (
                    <div className="flex items-center justify-between rounded-lg bg-muted p-3">
                      <span className="text-sm text-muted-foreground">Points Used</span>
                      <span className="font-medium">{loyaltyPoints.points_used}</span>
                    </div>
                  )}
                  
                  <Button variant="outline" className="w-full" asChild>
                    <Link href="/account/loyalty-points">
                      <TrendingUp className="mr-2 h-4 w-4" />
                      View History
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Referral Program */}
          {referralData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gift className="h-5 w-5 text-purple-500" />
                  Refer & Earn
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-lg bg-purple-50 p-4 dark:bg-purple-900/20">
                    <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
                      Your Referral Code
                    </p>
                    <p className="mt-2 text-2xl font-bold text-purple-600">
                      {referralData.referral_code}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-2xl font-bold">{referralData.total_referrals || 0}</p>
                      <p className="text-xs text-muted-foreground">Referrals</p>
                    </div>
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-2xl font-bold">{referralData.successful_referrals || 0}</p>
                      <p className="text-xs text-muted-foreground">Successful</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={handleCopyReferralCode}
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      Copy Code
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={handleShareReferral}
                    >
                      <Share2 className="mr-2 h-4 w-4" />
                      Share
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Quick Links</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" asChild>
                <a href="/account/orders">My Orders</a>
              </Button>
              <Button variant="outline" className="w-full justify-start" asChild>
                <a href="/account/addresses">Addresses</a>
              </Button>
              <Button variant="outline" className="w-full justify-start" asChild>
                <a href="/account/wishlist">Wishlist</a>
              </Button>
              {user?.is_vendor && (
                <Button variant="outline" className="w-full justify-start" asChild>
                  <a href="/vendor/dashboard">Vendor Dashboard</a>
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

