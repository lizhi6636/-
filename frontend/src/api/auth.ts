import client from './client';
import type { LoginPayload, RegisterPayload, TokenResponse, User } from '../types/auth';

export const authApi = {
  register: (data: RegisterPayload) =>
    client.post<User>('/auth/register', data),

  login: (data: LoginPayload) =>
    client.post<TokenResponse>('/auth/login', data),

  refresh: (refresh_token: string) =>
    client.post<TokenResponse>('/auth/refresh', { refresh_token }),

  getMe: () =>
    client.get<User>('/auth/me'),
};
