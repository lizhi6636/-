import { create } from 'zustand';

interface TradingStatus {
  status: string;
  is_trading: boolean;
  next_open?: string;
  next_close?: string;
  message: string;
}

interface ClockState {
  status: TradingStatus | null;
  setStatus: (status: TradingStatus) => void;
}

export const useClockStore = create<ClockState>((set) => ({
  status: null,
  setStatus: (status) => set({ status }),
}));
