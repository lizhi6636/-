export interface FactorDefinition {
  id: string;
  user_id: string | null;
  name: string;
  display_name: string;
  description?: string;
  expression: string;
  category: 'system' | 'custom' | 'technical' | 'fundamental';
  parameters: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface FactorAnalysis {
  factor_name: string;
  mean_ic: number;
  ic_ir: number;
  ic_std: number;
  positive_ic_ratio: number;
  num_stocks: number;
  ic_series: number[];
}
