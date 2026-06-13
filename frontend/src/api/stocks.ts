import client from './client';
import type { KlineData, RealtimeQuote, StockInfo, StockLinks } from '../types/stock';

export const stocksApi = {
  getStockDetail: (code: string) =>
    client.get<{ info: StockInfo; links: StockLinks }>(`/stocks/${code}`),

  getKline: (code: string, params: {
    period?: string;
    start_date?: string;
    end_date?: string;
    adjust?: string;
  }) =>
    client.get<{ code: string; period: string; data: KlineData[] }>(`/stocks/${code}/kline`, { params }),

  getRealtime: (code: string) =>
    client.get<RealtimeQuote>(`/stocks/${code}/realtime`),

  getFundamentals: (code: string) =>
    client.get<StockInfo>(`/stocks/${code}/fundamentals`),

  getLinks: (code: string) =>
    client.get<StockLinks>(`/stocks/${code}/links`),
};
