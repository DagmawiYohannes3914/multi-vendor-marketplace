'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Star, TrendingUp, TrendingDown, ArrowLeft, Clock } from 'lucide-react';
import { format } from 'date-fns';

const TRANSACTION_TYPES: Record<string, { icon: any; color: string; label: string }> = {
  earned: { icon: TrendingUp, color: 'text-green-600', label: 'Earned' },
  redeemed: { icon: TrendingDown, color: 'text-red-600', label: 'Redeemed' },
  expired: { icon: Clock, color: 'text-orange-600', label: 'Expired' },
};

export default function LoyaltyPointsPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);

  const { data: loyaltyData, isLoading } = useQuery({
    queryKey: ['loyalty-points'],
    queryFn: async () => {
      const response = await apiClient.getMyLoyaltyPoints();
      return response.data;
    },
    enabled: isAuthenticated && user?.is_customer,
  });

  if (!isAuthenticated || !user?.is_customer) {
    router.push('/auth/login');
    return null;
  }

  const transactions = Array.isArray(loyaltyData) ? loyaltyData : loyaltyData?.transactions || [];
  const totalPoints = loyaltyData?.total_points || 0;
  const pointsUsed = loyaltyData?.points_used || 0;
  const pointsExpiringSoon = loyaltyData?.points_expiring_soon || 0;

  return (
    <div className="container py-8">
      {/* Back Link */}
      <Link
        href="/account/profile"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Profile
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Loyalty Points</h1>
        <p className="mt-2 text-muted-foreground">
          Track your points and rewards history
        </p>
      </div>

      {/* Points Summary */}
      <div className="mb-8 grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Star className="h-5 w-5 text-yellow-500" />
              Available Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-cyan-600">{totalPoints}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingDown className="h-5 w-5 text-red-600" />
              Points Used
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-red-600">{pointsUsed}</p>
          </CardContent>
        </Card>

        {pointsExpiringSoon > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Clock className="h-5 w-5 text-orange-600" />
                Expiring Soon
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold text-orange-600">{pointsExpiringSoon}</p>
              <p className="mt-2 text-xs text-muted-foreground">Within 30 days</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Points History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : transactions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Star className="h-16 w-16 text-muted-foreground" />
              <h2 className="mt-4 text-xl font-semibold">No Points History</h2>
              <p className="mt-2 text-center text-muted-foreground">
                Start shopping to earn loyalty points!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {transactions.map((transaction: any) => {
                const type = TRANSACTION_TYPES[transaction.transaction_type] || TRANSACTION_TYPES.earned;
                const Icon = type.icon;

                return (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`rounded-full bg-muted p-2 ${type.color}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-medium">{transaction.description || type.label}</p>
                        <p className="text-sm text-muted-foreground">
                          {format(new Date(transaction.created_at), 'MMM d, yyyy h:mm a')}
                        </p>
                        {transaction.reference_id && (
                          <p className="text-xs text-muted-foreground">
                            Order #{transaction.reference_id.substring(0, 8)}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-xl font-bold ${type.color}`}>
                        {transaction.transaction_type === 'earned' ? '+' : '-'}
                        {transaction.points}
                      </p>
                      {transaction.expires_at && (
                        <p className="text-xs text-muted-foreground">
                          Expires {format(new Date(transaction.expires_at), 'MMM d, yyyy')}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>How Loyalty Points Work</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 text-sm text-muted-foreground">
            <div className="flex gap-3">
              <div className="flex-shrink-0">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-green-600 dark:bg-green-900/20">
                  1
                </div>
              </div>
              <div>
                <p className="font-medium text-foreground">Earn Points</p>
                <p>Get 1 point for every $1 spent on purchases</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-100 text-cyan-600 dark:bg-cyan-900/20">
                  2
                </div>
              </div>
              <div>
                <p className="font-medium text-foreground">Redeem Rewards</p>
                <p>Use 100 points = $1 off your next purchase</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-100 text-orange-600 dark:bg-orange-900/20">
                  3
                </div>
              </div>
              <div>
                <p className="font-medium text-foreground">Points Expiry</p>
                <p>Points expire 12 months after earning</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

