import { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card, Form, Input, Select, InputNumber, Button, Tabs, Table, Tag, message, Statistic, Spin, Alert, Typography, Tooltip } from 'antd';
import { LinkOutlined, RiseOutlined, FallOutlined, MinusOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Text } = Typography;

const api = axios.create({ baseURL: '/api/v1' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Open external stock page
function openStockLink(code: string) {
  const market = code.startsWith('6') || code.startsWith('5') || code.startsWith('9') ? 'sh' : 'sz';
  window.open(`https://quote.eastmoney.com/${market}${code}.html`, '_blank');
}

export default function SimulationPage() {
  const [account, setAccount] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [quotes, setQuotes] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [stockNameHint, setStockNameHint] = useState('');
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    try {
      setError('');
      const [a, p, o] = await Promise.all([
        api.get('/simulation/account'),
        api.get('/simulation/positions'),
        api.get('/simulation/orders'),
      ]);
      setAccount(a.data);
      const posData = Array.isArray(p.data) ? p.data : [];
      setPositions(posData);
      setOrders(Array.isArray(o.data) ? o.data : []);

      // Fetch real-time quotes for positions — merge with previous cache
      if (posData.length > 0) {
        const codes = posData.map((pos: any) => pos.stock_code);
        try {
          const qRes = await api.get('/market/quotes', { params: { codes: codes.join(',') } });
          const freshQuotes = qRes.data.quotes || {};
          // Merge: keep cached quotes for codes not in fresh response
          // (preserves last-known price when refresh fails partially)
          setQuotes(prev => ({ ...prev, ...freshQuotes }));
        } catch { /* quotes fetch is optional, keep previous quotes */ }
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || '数据加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const timer = setInterval(fetchData, 10000);
    return () => clearInterval(timer);
  }, [fetchData]);

  // Auto-fill stock name when user enters a valid stock code
  const lookupStockName = async (code: string) => {
    if (!code || code.length !== 6 || !/^\d{6}$/.test(code)) {
      setStockNameHint('');
      return;
    }
    // Check cache first
    if (quotes[code]?.name) {
      setStockNameHint(quotes[code].name);
      return;
    }
    try {
      const qRes = await api.get('/market/quotes', { params: { codes: code } });
      const name = qRes.data.quotes?.[code]?.name || '';
      setStockNameHint(name);
      // Merge into local quotes cache
      if (name) {
        setQuotes(prev => ({ ...prev, [code]: qRes.data.quotes[code] }));
      }
    } catch {
      setStockNameHint('');
    }
  };

  const placeOrder = async (values: any) => {
    setSubmitting(true);
    try {
      await api.post('/simulation/orders', {
        stock_code: values.stock_code,
        direction: values.direction,
        order_type: values.order_type,
        limit_price: values.order_type === 'limit' ? values.limit_price : undefined,
        quantity: values.quantity,
      });
      message.success('下单成功！');
      await fetchData();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '下单失败');
    } finally {
      setSubmitting(false);
    }
  };

  const cancelOrder = async (id: string) => {
    try {
      await api.delete(`/simulation/orders/${id}`);
      message.success('已撤单');
      await fetchData();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '撤单失败');
    }
  };

  // Calculate position P&L
  // Priority: realtime quote price → last cached quote price → position.current_price → 0
  const calcPnL = (pos: any) => {
    const q = quotes[pos.stock_code];
    // Use cached quote price if available (even if stale); only fall back to
    // pos.current_price when we've never fetched a quote for this code.
    const currentPrice = (q && q.price > 0) ? q.price : Number(pos.current_price) || 0;
    const cost = Number(pos.avg_cost) || 0;
    const qty = pos.quantity || 0;
    if (!cost || !qty) return { pnl: 0, pnlPct: 0, price: currentPrice, changePct: q?.change_pct || 0 };
    const pnl = (currentPrice - cost) * qty;
    const pnlPct = ((currentPrice - cost) / cost) * 100;
    return { pnl, pnlPct, price: currentPrice, changePct: q?.change_pct || 0 };
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" tip="加载中..." /></div>;

  return (
    <div>
      {error && <Alert type="error" message={error} closable style={{ marginBottom: 12 }} onClose={() => setError('')} />}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card title="下单面板" size="small">
            <Form form={form} layout="vertical" onFinish={placeOrder} size="small">
              <Form.Item name="stock_code" label="股票代码" rules={[{ required: true, pattern: /^\d{6}$/, message: '请输入6位代码' }]}>
                <Input placeholder="如: 000001" maxLength={6}
                  onBlur={(e) => lookupStockName(e.target.value)}
                  onChange={() => setStockNameHint('')}
                />
              </Form.Item>
              {stockNameHint && (
                <div style={{ marginTop: -16, marginBottom: 16, color: '#52c41a', fontSize: 12 }}>
                  识别为：{stockNameHint}
                </div>
              )}
              <Form.Item name="direction" label="买卖方向" initialValue="buy">
                <Select options={[{ value: 'buy', label: '买入' }, { value: 'sell', label: '卖出' }]} />
              </Form.Item>
              <Form.Item name="order_type" label="订单类型" initialValue="market">
                <Select options={[{ value: 'market', label: '市价单' }, { value: 'limit', label: '限价单' }]} />
              </Form.Item>
              <Form.Item name="quantity" label="数量(股)" rules={[{ required: true }]}>
                <InputNumber min={100} step={100} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={submitting} block>确认下单</Button>
              </Form.Item>
            </Form>
            {account && (
              <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 12 }}>
                <Statistic title="可用资金" value={Number(account.cash || 0)} precision={2} prefix="¥" />
                <Statistic title="总资产" value={Number(account.total_asset || 0)} precision={2} prefix="¥" />
                <div style={{ marginTop: 4 }}>
                  <Text type="secondary">
                    总收益{' '}
                    <Text style={{ color: Number(account.total_pnl) >= 0 ? '#cf1322' : '#3f8600', fontWeight: 'bold' }}>
                      {Number(account.total_pnl || 0) >= 0 ? '+' : ''}{Number(account.total_pnl || 0).toFixed(2)}
                    </Text>
                    {' '}({account.total_return_pct || 0}%)
                  </Text>
                </div>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Card size="small">
            <Tabs items={[
              {
                key: 'positions', label: `持仓 (${positions.length})`,
                children: (
                  <Table dataSource={positions} rowKey="id" size="small" pagination={false} scroll={{ x: 650 }}
                    columns={[
                      { title: '代码', dataIndex: 'stock_code', width: 80 },
                      { title: '名称', dataIndex: 'stock_name', width: 90, render: (v: string, r: any) => v || quotes[r.stock_code]?.name || '-' },
                      { title: '持仓', dataIndex: 'quantity', width: 70 },
                      { title: '可用', dataIndex: 'available_quantity', width: 70 },
                      {
                        title: '成本', dataIndex: 'avg_cost', width: 80,
                        render: (v: any) => Number(v || 0).toFixed(2),
                      },
                      {
                        title: '现价', width: 80,
                        render: (_: any, r: any) => {
                          const { price, changePct } = calcPnL(r);
                          const color = changePct > 0 ? '#cf1322' : changePct < 0 ? '#3f8600' : '#666';
                          return <span style={{ color, fontWeight: 500 }}>{price ? price.toFixed(2) : '-'}</span>;
                        },
                      },
                      {
                        title: <Tooltip title="(现价 - 昨收) / 昨收 × 100%">涨跌幅 ▾</Tooltip>, width: 85,
                        render: (_: any, r: any) => {
                          const { changePct } = calcPnL(r);
                          const icon = changePct > 0 ? <RiseOutlined /> : changePct < 0 ? <FallOutlined /> : <MinusOutlined />;
                          const color = changePct > 0 ? '#cf1322' : changePct < 0 ? '#3f8600' : '#666';
                          return <span style={{ color }}>{icon} {changePct > 0 ? '+' : ''}{changePct.toFixed(2)}%</span>;
                        },
                      },
                      {
                        title: '盈亏', width: 100,
                        render: (_: any, r: any) => {
                          const { pnl, pnlPct } = calcPnL(r);
                          const color = pnl >= 0 ? '#cf1322' : '#3f8600';
                          return (
                            <span style={{ color, whiteSpace: 'nowrap' }}>
                              {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
                              <span style={{ fontSize: 11, marginLeft: 2 }}>({pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%)</span>
                            </span>
                          );
                        },
                      },
                      {
                        title: '操作', width: 80,
                        render: (_: any, r: any) => (
                          <Tooltip title="在东方财富查看">
                            <Button size="small" type="link" icon={<LinkOutlined />}
                              onClick={() => openStockLink(r.stock_code)}>
                              查看
                            </Button>
                          </Tooltip>
                        ),
                      },
                    ]}
                    locale={{ emptyText: '暂无持仓' }}
                    summary={() => {
                      if (!positions.length) return null;
                      let totalPnL = 0, totalMarketVal = 0;
                      positions.forEach((p: any) => {
                        const { pnl, price } = calcPnL(p);
                        totalPnL += pnl;
                        totalMarketVal += price * p.quantity;
                      });
                      return (
                        <Table.Summary.Row>
                          <Table.Summary.Cell index={0} colSpan={4}>
                            <Text strong>合计</Text>
                          </Table.Summary.Cell>
                          <Table.Summary.Cell index={1} colSpan={3}>
                            <Text strong>市值 ¥{totalMarketVal.toFixed(2)}</Text>
                          </Table.Summary.Cell>
                          <Table.Summary.Cell index={2}>
                            <Text strong style={{ color: totalPnL >= 0 ? '#cf1322' : '#3f8600' }}>
                              {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
                            </Text>
                          </Table.Summary.Cell>
                          <Table.Summary.Cell index={3} />
                        </Table.Summary.Row>
                      );
                    }}
                  />
                ),
              },
              {
                key: 'orders', label: `委托 (${orders.length})`,
                children: (
                  <Table dataSource={orders} rowKey="id" size="small" pagination={false}
                    columns={[
                      { title: '代码', dataIndex: 'stock_code', width: 80 },
                      { title: '方向', dataIndex: 'direction', width: 55, render: (v: string) => <Tag color={v === 'buy' ? 'red' : 'green'}>{v === 'buy' ? '买入' : '卖出'}</Tag> },
                      { title: '类型', dataIndex: 'order_type', width: 55, render: (v: string) => v === 'market' ? '市价' : '限价' },
                      { title: '价格', dataIndex: 'limit_price', width: 75, render: (v: any) => v ? Number(v).toFixed(2) : '市价' },
                      { title: '数量', dataIndex: 'quantity', width: 65 },
                      { title: '成交', dataIndex: 'filled_quantity', width: 65 },
                      { title: '状态', dataIndex: 'status', width: 75, render: (v: string) => {
                        const m: any = { pending: '待成交', partial: '部分', filled: '已成', cancelled: '已撤', rejected: '拒绝' };
                        const c: any = { pending: 'blue', partial: 'orange', filled: 'green', cancelled: 'default', rejected: 'red' };
                        return <Tag color={c[v]}>{m[v] || v}</Tag>;
                      }},
                      { title: '时间', dataIndex: 'created_at', width: 140, render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
                      { title: '操作', width: 60, render: (_: any, r: any) => (
                        (r.status === 'pending' || r.status === 'partial') && (
                          <Button size="small" danger onClick={() => cancelOrder(r.id)}>撤单</Button>
                        )
                      )},
                    ]}
                    locale={{ emptyText: '暂无委托' }}
                  />
                ),
              },
            ]} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
