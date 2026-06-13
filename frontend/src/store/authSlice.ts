import { create } from 'zustand';
import { authApi } from '../api/auth';
import type { User, LoginPayload, RegisterPayload } from '../types/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;

  login: (data: LoginPayload) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,

  login: async (data) => {
    set({ loading: true });
    try {
      const response = await authApi.login(data);
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      set({ isAuthenticated: true, loading: false });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  register: async (data) => {
    set({ loading: true });
    try {
      await authApi.register(data);
      set({ loading: false });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const response = await authApi.getMe();
      set({ user: response.data, isAuthenticated: true });
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  setUser: (user) => set({ user }),
}));
