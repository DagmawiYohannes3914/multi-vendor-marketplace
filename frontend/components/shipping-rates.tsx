'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent } from '@/components/ui/card';
import { Truck, Clock } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { addBusinessDays, format } from 'date-fns';

interface ShippingRatesProps {
  selectedRate: string | null;
  onSelectRate: (rateId: string, cost: number) => void;
}

export function ShippingRates({ selectedRate, onSelectRate }: ShippingRatesProps) {
  const { data: rates, isLoading } = useQuery({
    queryKey: ['shipping-rates'],
    queryFn: async () => {
      const response = await apiClient.getShippingRates({ is_active: true });
      return response.data;
    },
  });

  const calculateDeliveryDate = (minDays: number, maxDays: number) => {
    const today = new Date();
    const minDate = addBusinessDays(today, minDays);
    const maxDate = addBusinessDays(today, maxDays);
    
    if (minDays === maxDays) {
      return `Arrives by ${format(maxDate, 'EEE, MMM d')}`;
    }
    return `Arrives ${format(minDate, 'MMM d')} - ${format(maxDate, 'MMM d')}`;
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  const ratesList = Array.isArray(rates) ? rates : rates?.results || [];

  if (ratesList.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-sm text-muted-foreground">
            No shipping options available
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {ratesList.map((rate: any) => (
        <label
          key={rate.id}
          className={`flex cursor-pointer items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent ${
            selectedRate === rate.id ? 'border-primary bg-accent' : ''
          }`}
        >
          <input
            type="radio"
            name="shipping"
            value={rate.id}
            checked={selectedRate === rate.id}
            onChange={() => onSelectRate(rate.id, parseFloat(rate.base_cost))}
            className="h-4 w-4"
          />
          <Truck className="h-5 w-5 text-muted-foreground" />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">{rate.carrier}</p>
                <p className="text-sm text-muted-foreground">{rate.service_name}</p>
              </div>
              <p className="text-lg font-bold text-cyan-600">
                {formatPrice(rate.base_cost)}
              </p>
            </div>
            <div className="mt-2 space-y-1">
              <div className="flex items-center gap-2 text-sm font-medium text-cyan-600 dark:text-cyan-400">
                <Clock className="h-4 w-4" />
                <span>{calculateDeliveryDate(rate.min_delivery_days, rate.max_delivery_days)}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {rate.min_delivery_days}-{rate.max_delivery_days} business days
              </p>
            </div>
          </div>
        </label>
      ))}
    </div>
  );
}

