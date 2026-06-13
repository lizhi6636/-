import client from './client';
import type { BacktestCreate, BacktestTask } from '../types/backtest';

export const backtestApi = {
  createTask: (data: BacktestCreate) =>
    client.post<BacktestTask>('/backtest/tasks', data),

  getTasks: (page = 1, pageSize = 20) =>
    client.get<BacktestTask[]>('/backtest/tasks', { params: { page, page_size: pageSize } }),

  getTask: (taskId: string) =>
    client.get<BacktestTask>(`/backtest/tasks/${taskId}`),

  getTaskResults: (taskId: string) =>
    client.get(`/backtest/tasks/${taskId}/results`),
};
