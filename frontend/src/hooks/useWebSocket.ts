import { useEffect, useRef, useCallback } from 'react';
import { useMarketStore } from '../store/marketSlice';

export function useWebSocket(codes: string[]) {
  const wsRef = useRef<WebSocket | null>(null);
  const updateQuote = useMarketStore((s) => s.updateQuote);

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/market?token=${token}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (codes.length > 0) {
        ws.send(JSON.stringify({ action: 'subscribe', codes }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.code) {
          updateQuote(data.code, data);
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
  }, [codes, updateQuote]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  // Update subscriptions when codes change
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && codes.length > 0) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', codes }));
    }
  }, [codes]);
}
