export interface User {
  id: string;
  email: string;
  username: string;
  is_verified: boolean;
  cash: string;
  initial_capital: string;
  created_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
