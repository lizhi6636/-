import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Tabs, Descriptions, Spin, Typography, Tag } from 'antd';
import { stocksApi } from '../../api/stocks';
import KLineChart from '../../components/charts/KLineChart';
import StockLinkBar from '../../components/trading/StockLinkBar';
import type { KlineData, StockInfo } from '../../types/stock';

const { Title, Text } = Typography;

export default function StockDetailPage() {
  const { code } = useParams<{ code: string }>();
  const [loading, setLoading] = useState(true);
  const [info, setInfo] = useState<StockInfo | null>(null);
  const [klineData, setKlineData] = useState<KlineData[]>([]);
  const [period, setPeriod] = useState('daily');

  useEffect(() => {
    if (!code) return;
    setLoading(true);

    Promise.all([
      stocksApi.getStockDetail(code),
      stocksApi.getKline(code, { period, adjust: 'qfq' }),
    ]).then(([detailRes, klineRes]) => {
      setInfo(detailRes.data.info);
      setKlineData(klineRes.data.data || []);
    }).finally(() => setLoading(false));
  }, [code, period]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      {/* Header */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>
              {info?.name || code}
              <Tag style={{ marginLeft: 8 }}>{info?.market || ''}</Tag>
            </Title>
            <Text type="secondary" style={{ fontSize: 16 }}>{code}</Text>
          </div>
          <StockLinkBar code={code || ''} />
        </div>
      </Card>

      <Tabs
        defaultActiveKey="kline"
        items={[
          {
            key: 'kline',
            label: 'K线图',
            children: (
              <Card>
                <div style={{ marginBottom: 12 }}>
                  <Tabs
                    activeKey={period}
                    onChange={setPeriod}
                    size="small"
                    items={[
                      { key: 'daily', label: '日K' },
                      { key: 'weekly', label: '周K' },
                      { key: 'monthly', label: '月K' },
                    ]}
                  />
                </div>
                {klineData.length > 0 ? (
                  <KLineChart data={klineData} height={500} />
                ) : (
                  <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
                    暂无K线数据
                  </div>
                )}
              </Card>
            ),
          },
          {
            key: 'fundamentals',
            label: '基本面',
            children: (
              <Card>
                <Descriptions column={2} bordered size="small">
                  <Descriptions.Item label="股票名称">{info?.name || '-'}</Descriptions.Item>
                  <Descriptions.Item label="股票代码">{code}</Descriptions.Item>
                  <Descriptions.Item label="市盈率(动态)">
                    {info?.pe ? info.pe.toFixed(2) : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="市净率">
                    {info?.pb ? info.pb.toFixed(2) : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="总市值">
                    {info?.market_cap ? `${(info.market_cap / 1e8).toFixed(2)}亿` : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="市场">{info?.market || '-'}</Descriptions.Item>
                </Descriptions>
              </Card>
            ),
          },
          {
            key: 'links',
            label: '外部链接',
            children: (
              <Card>
                <StockLinkBar code={code || ''} />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    点击上方按钮跳转到外部平台查看更多数据。
                    移动端用户可尝试打开App版链接。
                  </Text>
                </div>
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
}
