export interface KlineData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
  amplitude: number;
  change_pct: number;
  change_amount: number;
  turnover: number;
}

export interface RealtimeQuote {
  code: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  open: number;
  high: number;
  low: number;
  pre_close: number;
  volume: number;
  amount: number;
  update_time: string;
}

export interface StockInfo {
  code: string;
  name: string;
  market: string;
  pe?: number;
  pb?: number;
  market_cap?: number;
  total_shares?: number;
}

export interface IndexData {
  name: string;
  code: string;
  price: number;
  change: number;
  change_pct: number;
}

export interface StockLinks {
  eastmoney: string;
  tonghuashun_web: string;
  xueqiu: string;
  eastmoney_app: string;
  tonghuashun_app: string;
  xueqiu_app: string;
}
