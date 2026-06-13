export function formatPrice(price: number | string, decimals = 2): string {
  const num = typeof price === 'string' ? parseFloat(price) : price;
  if (isNaN(num)) return '-';
  return num.toFixed(decimals);
}

export function formatPercent(pct: number, decimals = 2): string {
  if (isNaN(pct)) return '-';
  const sign = pct >= 0 ? '+' : '';
  return `${sign}${pct.toFixed(decimals)}%`;
}

export function formatMoney(amount: number | string, decimals = 2): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '-';
  if (Math.abs(num) >= 1e8) {
    return `${(num / 1e8).toFixed(decimals)}亿`;
  }
  if (Math.abs(num) >= 1e4) {
    return `${(num / 1e4).toFixed(decimals)}万`;
  }
  return num.toFixed(decimals);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return `${formatDate(dateStr)} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}
