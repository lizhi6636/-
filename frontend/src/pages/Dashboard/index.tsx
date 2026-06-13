import { useState, useEffect, useCallback } from 'react';
import {
  Row, Col, Card, Statistic, Table, Button, Space, Input, message,
  Typography, Spin, Tooltip,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, ArrowUpOutlined, ArrowDownOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { dashboardApi } from '../../api/dashboard';
import { useMarketStore } from '../../store/marketSlice';
import { usePolling } from '../../hooks/usePolling';
import RefreshSelector from '../../components/trading/RefreshSelector';
import PnLChart from '../../components/charts/PnLChart';
import type { IndexData, RealtimeQuote } from '../../types/stock';
import type { AccountSummary } from '../../types/simulation';

const { Text } = Typography;

export default function DashboardPage() {
  const [indices, setIndices] = useState<IndexData[]>([]);
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [newCode, setNewCode] = useState('');
  const [nameHint, setNameHint] = useState('');
  const refreshInterval = useMarketStore((s) => s.refreshInterval);

  const fetchData = useCallback(async () => {
    try {
      const res = await dashboardApi.getOverview();
      setIndices(res.data.indices || []);
      setWatchlist(res.data.watchlist || []);
      setAccount(res.data.account_summary || null);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  usePolling(fetchData, refreshInterval === 'ws' ? 'manual' : refreshInterval);

  // Lookup stock name for the entered code
  const lookupStockName = async (code: string) => {
    if (!code || code.length !== 6) { setNameHint(''); return; }
    try {
      const res = await dashboardApi.getQuotes([code]);
      const name = res.data.quotes?.[code]?.name || '';
      setNameHint(name);
    } catch { setNameHint(''); }
  };

  const handleAddWatchlist = async () => {
    if (!newCode || newCode.length !== 6) {
      message.warning('请输入6位股票代码');
      return;
    }
    try {
      await dashboardApi.addToWatchlist({ stock_code: newCode, stock_name: nameHint || undefined });
      message.success('已添加');
      setNewCode('');
      setNameHint('');
      fetchData();
    } catch {
      message.error('添加失败');
    }
  };

  const handleRemoveWatchlist = async (id: string) => {
    try {
      await dashboardApi.removeFromWatchlist(id);
      message.success('已移除');
      fetchData();
    } catch {
      message.error('移除失败');
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <Row gutter={[16, 16]}>
        {/* Market indices */}
        {indices.map((idx) => (
          <Col xs={24} sm={8} key={idx.code}>
            <Card className="dashboard-card" size="small">
              <Statistic
                title={idx.name}
                value={idx.price}
                precision={2}
                valueStyle={{ color: idx.change >= 0 ? '#cf1322' : '#3f8600' }}
                prefix={idx.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix={
                  <Tooltip title="较昨日收盘价涨跌幅">
                    <Text type={idx.change_pct >= 0 ? 'danger' : 'success'}>
                      {idx.change_pct >= 0 ? '+' : ''}{idx.change_pct?.toFixed(2)}%
                    </Text>
                  </Tooltip>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Account Summary */}
        <Col xs={24} lg={8}>
          <Card title="账户概览" size="small" className="dashboard-card">
            {account ? (
              <>
                <Statistic title="总资产" value={Number(account.total_asset || 0)} precision={2} prefix="¥" />
                <Statistic title="可用资金" value={Number(account.cash || 0)} precision={2} prefix="¥" />
                <Statistic
                  title="总收益"
                  value={Number(account.total_pnl || 0)}
                  precision={2}
                  valueStyle={{ color: Number(account.total_pnl) >= 0 ? '#cf1322' : '#3f8600' }}
                  prefix={Number(account.total_pnl) >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  suffix={`(${account.total_return_pct}%)`}
                />
              </>
            ) : (
              <Text type="secondary">加载中...</Text>
            )}
          </Card>
        </Col>

        {/* Watchlist */}
        <Col xs={24} lg={16}>
          <Card
            title="自选股"
            size="small"
            className="dashboard-card"
            extra={<RefreshSelector />}
          >
            <Space style={{ marginBottom: 12 }} align="start">
              <div>
                <Input
                  placeholder="股票代码 (如: 000001)"
                  value={newCode}
                  onChange={(e) => { setNewCode(e.target.value); setNameHint(''); }}
                  onBlur={(e) => lookupStockName(e.target.value)}
                  style={{ width: 160 }}
                  maxLength={6}
                />
                {nameHint && (
                  <div style={{ color: '#52c41a', fontSize: 11, marginTop: 2 }}>{nameHint}</div>
                )}
              </div>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddWatchlist}>
                添加
              </Button>
            </Space>

            <Table
              dataSource={watchlist}
              rowKey="id"
              size="small"
              pagination={false}
              scroll={{ x: 400 }}
              columns={[
                { title: '代码', dataIndex: 'stock_code', width: 90 },
                { title: '名称', dataIndex: 'stock_name', width: 100 },
                {
                  title: '最新价', dataIndex: 'price', width: 80,
                  render: (v: number) => v ? v.toFixed(2) : '-',
                },
                {
                  title: <Tooltip title="(最新价 - 昨日收盘价) / 昨日收盘价 × 100%">涨跌幅 ▾</Tooltip>, dataIndex: 'change_pct', width: 100,
                  render: (v: number) => (
                    <Text type={v >= 0 ? 'danger' : 'success'}>
                      {v >= 0 ? '+' : ''}{v?.toFixed(2)}%
                    </Text>
                  ),
                },
                {
                  title: '操作', width: 80,
                  render: (_: any, record: any) => (
                    <Button
                      type="link"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => handleRemoveWatchlist(record.id)}
                    />
                  ),
                },
              ]}
              locale={{ emptyText: '暂无自选股，请添加' }}
            />
          </Card>
        </Col>
      </Row>

      {/* P&L Chart placeholder */}
      <Card title="账户权益曲线" style={{ marginTop: 16 }} className="dashboard-card">
        <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
          <Text type="secondary">
            完成一笔交易后，权益曲线将在此展示
          </Text>
        </div>
      </Card>
    </div>
  );
}
