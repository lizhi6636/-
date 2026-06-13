import client from './client';
import type { FactorDefinition, FactorAnalysis } from '../types/factor';

export const factorApi = {
  listFactors: (category?: string) =>
    client.get<FactorDefinition[]>('/factors', { params: { category } }),

  createFactor: (data: Partial<FactorDefinition>) =>
    client.post<FactorDefinition>('/factors', data),

  updateFactor: (id: string, data: Partial<FactorDefinition>) =>
    client.put<FactorDefinition>(`/factors/${id}`, data),

  deleteFactor: (id: string) =>
    client.delete(`/factors/${id}`),

  previewFactor: (data: { expression: string; stock_code: string; start_date: string; end_date: string }) =>
    client.post('/factors/preview', data),

  runAnalysis: (data: { factor_id: string; stock_codes: string[]; start_date: string; end_date: string }) =>
    client.post<FactorAnalysis>('/factors/analysis', data),
};
