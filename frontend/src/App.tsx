import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from './store/authSlice';
import { authApi } from './api/auth';
import AppLayout from './components/Layout/AppLayout';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import DashboardPage from './pages/Dashboard';
import StockDetailPage from './pages/StockDetail';
import BacktestPage from './pages/Backtest';
import FactorPage from './pages/Factor';
import SimulationPage from './pages/Simulation';
import LearnPage from './pages/Learn';

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <AppLayout />;
}

function AppInit() {
  const setUser = useAuthStore((s) => s.setUser);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    // On app load, try to refresh token for silent auto-login
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      authApi.refresh(refreshToken)
        .then((res) => {
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          useAuthStore.setState({ isAuthenticated: true });
          return authApi.getMe();
        })
        .then((userRes) => {
          if (userRes) setUser(userRes.data);
        })
        .catch(() => {
          // Refresh failed — clear tokens, user needs to login again
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          useAuthStore.setState({ isAuthenticated: false });
        })
        .finally(() => setInitializing(false));
    } else {
      // No refresh token — stay on login
      setInitializing(false);
    }
  }, []);

  if (initializing) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5' }}>
        <Spin size="large" tip="自动登录中..." />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/stock/:code" element={<StockDetailPage />} />
        <Route path="/backtest" element={<BacktestPage />} />
        <Route path="/factor" element={<FactorPage />} />
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/learn" element={<LearnPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInit />
    </BrowserRouter>
  );
}
