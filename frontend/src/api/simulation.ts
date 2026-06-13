import client from './client';
import type { OrderCreate, Order, Trade, Position, AccountSummary } from '../types/simulation';

export const simulationApi = {
  createOrder: (data: OrderCreate) =>
    client.post<Order>('/simulation/orders', data),

  getOrders: (status?: string) =>
    client.get<Order[]>('/simulation/orders', { params: { status } }),

  cancelOrder: (orderId: string) =>
    client.delete(`/simulation/orders/${orderId}`),

  getPositions: () =>
    client.get<Position[]>('/simulation/positions'),

  getTrades: (page = 1, pageSize = 20) =>
    client.get<Trade[]>('/simulation/trades', { params: { page, page_size: pageSize } }),

  getAccount: () =>
    client.get<AccountSummary>('/simulation/account'),
};
