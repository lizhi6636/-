import client from './client';
import type { IndexData } from '../types/stock';

export const dashboardApi = {
  getOverview: () =>
    client.get('/dashboard/overview'),

  getAccountSummary: () =>
    client.get('/dashboard/account-summary'),

  getWatchlist: () =>
    client.get('/dashboard/watchlist'),

  addToWatchlist: (data: { stock_code: string; stock_name?: string }) =>
    client.post('/dashboard/watchlist', data),

  removeFromWatchlist: (id: string) =>
    client.delete(`/dashboard/watchlist/${id}`),

  getIndices: () =>
    client.get<{ indices: IndexData[] }>('/market/indices'),

  getQuotes: (codes: string[]) =>
    client.get('/market/quotes', { params: { codes: codes.join(',') } }),

  getTradingStatus: () =>
    client.get('/market/trading-status'),
};
