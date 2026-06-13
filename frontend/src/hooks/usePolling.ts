import { useEffect, useRef } from 'react';

type IntervalOption = '5s' | '15s' | '30s' | '1min' | 'manual';

const INTERVAL_MAP: Record<IntervalOption, number> = {
  '5s': 5000,
  '15s': 15000,
  '30s': 30000,
  '1min': 60000,
  'manual': 0,
};

export function usePolling(
  callback: () => void,
  interval: IntervalOption | 'ws',
  enabled = true
) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (interval === 'ws' || interval === 'manual' || !enabled) return;

    const ms = INTERVAL_MAP[interval];
    if (!ms) return;

    // Initial call
    savedCallback.current();

    const id = setInterval(() => savedCallback.current(), ms);
    return () => clearInterval(id);
  }, [interval, enabled]);
}
