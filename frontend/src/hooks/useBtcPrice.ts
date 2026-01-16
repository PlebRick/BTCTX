import { useState, useEffect, useCallback } from 'react';
import api from '../api';

type PriceMode = 'auto' | 'manual' | 'date';

interface UseBtcPriceOptions {
  mode?: PriceMode;
  date?: string;
  refreshInterval?: number; // in ms, only for auto mode
  initialPrice?: number;
}

interface UseBtcPriceReturn {
  price: number;
  isLoading: boolean;
  error: string | null;
  setPrice: (price: number) => void;
  refresh: () => Promise<void>;
}

/**
 * Custom hook for fetching and managing BTC price
 *
 * Modes:
 * - 'auto': Fetches live price and optionally refreshes at interval
 * - 'manual': Uses initial price or allows manual setting
 * - 'date': Fetches historical price for a specific date
 */
export function useBtcPrice(options: UseBtcPriceOptions = {}): UseBtcPriceReturn {
  const {
    mode = 'auto',
    date,
    refreshInterval = 0, // 0 means no auto-refresh
    initialPrice = 0,
  } = options;

  const [price, setPrice] = useState<number>(initialPrice);
  const [isLoading, setIsLoading] = useState<boolean>(mode !== 'manual');
  const [error, setError] = useState<string | null>(null);

  const fetchLivePrice = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.get<LiveBtcPriceResponse>('/bitcoin/price');
      if (res.data && typeof res.data.USD === 'number') {
        setPrice(res.data.USD);
      } else {
        setError('Invalid price response');
      }
    } catch {
      setError('Failed to fetch BTC price');
      setPrice(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchHistoricalPrice = useCallback(async (dateStr: string) => {
    if (!dateStr) return;

    setIsLoading(true);
    setError(null);
    try {
      const res = await api.get<LiveBtcPriceResponse>(
        `/bitcoin/price/history?date=${dateStr}`
      );
      if (res.data && typeof res.data.USD === 'number') {
        setPrice(res.data.USD);
      } else {
        setError('Invalid historical price response');
      }
    } catch {
      setError('Failed to fetch historical BTC price');
      setPrice(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto mode: fetch live price
  useEffect(() => {
    if (mode !== 'auto') return;

    fetchLivePrice();

    // Set up interval if specified
    if (refreshInterval > 0) {
      const intervalId = setInterval(fetchLivePrice, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [mode, refreshInterval, fetchLivePrice]);

  // Date mode: fetch historical price
  useEffect(() => {
    if (mode !== 'date' || !date) return;
    fetchHistoricalPrice(date);
  }, [mode, date, fetchHistoricalPrice]);

  // Manual mode: fetch once to seed price if no initial price
  useEffect(() => {
    if (mode !== 'manual') return;
    if (initialPrice === 0) {
      fetchLivePrice();
    }
  }, [mode, initialPrice, fetchLivePrice]);

  const refresh = useCallback(async () => {
    if (mode === 'date' && date) {
      await fetchHistoricalPrice(date);
    } else {
      await fetchLivePrice();
    }
  }, [mode, date, fetchLivePrice, fetchHistoricalPrice]);

  return {
    price,
    isLoading,
    error,
    setPrice,
    refresh,
  };
}

/**
 * Simple hook for just getting live BTC price (most common use case)
 */
export function useLiveBtcPrice(refreshInterval = 0): UseBtcPriceReturn {
  return useBtcPrice({ mode: 'auto', refreshInterval });
}

/**
 * Hook for getting historical BTC price for a specific date
 */
export function useHistoricalBtcPrice(date: string): UseBtcPriceReturn {
  return useBtcPrice({ mode: 'date', date });
}

export default useBtcPrice;
