export interface BacktestCreate {
  name: string;
  strategy_code: string;
  stock_codes: string[];
  start_date: string;
  end_date: string;
  initial_capital: string;
  parameters: Record<string, unknown>;
}

export interface BacktestTask {
  id: string;
  user_id: string;
  name: string;
  stock_codes: string[];
  start_date: string;
  end_date: string;
  initial_capital: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  metrics: Record<string, unknown> | null;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}
