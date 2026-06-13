export interface OrderCreate {
  stock_code: string;
  direction: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  limit_price?: number;
  quantity: number;
}

export interface Order {
  id: string;
  user_id: string;
  stock_code: string;
  stock_name: string;
  order_type: string;
  direction: string;
  limit_price: number | null;
  quantity: number;
  filled_quantity: number;
  status: 'pending' | 'partial' | 'filled' | 'cancelled' | 'rejected';
  commission: string;
  stamp_tax: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface Trade {
  id: string;
  order_id: string;
  stock_code: string;
  stock_name: string;
  direction: string;
  price: string;
  quantity: number;
  commission: string;
  stamp_tax: string;
  traded_at: string;
}

export interface Position {
  id: string;
  stock_code: string;
  stock_name: string;
  quantity: number;
  available_quantity: number;
  avg_cost: string;
  current_price: number | null;
  updated_at: string;
}

export interface AccountSummary {
  total_asset: string;
  cash: string;
  market_value: string;
  total_pnl: string;
  daily_pnl: string;
  initial_capital: string;
  total_return_pct: number;
}
