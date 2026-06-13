import { create } from 'zustand';
import type { RealtimeQuote } from '../types/stock';

type RefreshInterval = 'ws' | '5s' | '15s' | '30s' | '1min' | 'manual';

interface MarketState {
  quotes: Record<string, RealtimeQuote>;
  refreshInterval: RefreshInterval;
  lastUpdate: number | null;

  setRefreshInterval: (interval: RefreshInterval) => void;
  updateQuote: (code: string, quote: RealtimeQuote) => void;
  updateQuotes: (quotes: RealtimeQuote[]) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  quotes: {},
  refreshInterval: 'ws',
  lastUpdate: null,

  setRefreshInterval: (interval) => set({ refreshInterval: interval }),

  updateQuote: (code, quote) =>
    set((state) => ({
      quotes: { ...state.quotes, [code]: quote },
      lastUpdate: Date.now(),
    })),

  updateQuotes: (quotes) =>
    set((state) => {
      const newQuotes = { ...state.quotes };
      quotes.forEach((q) => {
        newQuotes[q.code] = q;
      });
      return { quotes: newQuotes, lastUpdate: Date.now() };
    }),
}));
