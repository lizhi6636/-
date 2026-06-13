import { useState, useEffect } from 'react';
import {
  Card, Tabs, List, Typography, Tag, Spin, Empty, Divider,
} from 'antd';
import {
  ReadOutlined, CodeOutlined, ApiOutlined, EyeOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const { Text, Title, Paragraph } = Typography;

interface Article {
  id: string;
  title: string;
  category: string;
  summary: string;
  content: string;
  tags: string[];
  view_count: number;
  created_at: string;
}

export default function LearnPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [cases, setCases] = useState<Article[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [artRes, caseRes] = await Promise.all([
          axios.get('/api/v1/learn/articles'),
          axios.get('/api/v1/learn/cases'),
        ]);
        setArticles(artRes.data || []);
        setCases(caseRes.data || []);
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchData();
  }, []);

  const fetchArticleDetail = async (id: string) => {
    try {
      const res = await axios.get(`/api/v1/learn/articles/${id}`);
      setSelectedArticle(res.data);
    } catch { /* ignore */ }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      {selectedArticle ? (
        <Card
          title={selectedArticle.title}
          extra={<a onClick={() => setSelectedArticle(null)}>返回列表</a>}
        >
          <div style={{ maxWidth: 800, margin: '0 auto', padding: '16px 0' }}>
            <div style={{ marginBottom: 16 }}>
              {selectedArticle.tags?.map((tag: string) => (
                <Tag key={tag}>{tag}</Tag>
              ))}
              <Text type="secondary" style={{ marginLeft: 8 }}>
                <EyeOutlined /> {selectedArticle.view_count} 次阅读
              </Text>
            </div>
            <Divider />
            <div className="markdown-content">
              <ReactMarkdown>{selectedArticle.content}</ReactMarkdown>
            </div>
          </div>
        </Card>
      ) : (
        <Tabs
          defaultActiveKey="knowledge"
          items={[
            {
              key: 'knowledge',
              label: <span><ReadOutlined /> 知识库</span>,
              children: (
                <Card>
                  <List
                    dataSource={articles}
                    renderItem={(item: Article) => (
                      <List.Item
                        style={{ cursor: 'pointer' }}
                        onClick={() => fetchArticleDetail(item.id)}
                      >
                        <List.Item.Meta
                          title={item.title}
                          description={
                            <>
                              <Text type="secondary">{item.summary}</Text>
                              <div style={{ marginTop: 4 }}>
                                {item.tags?.map((tag: string) => (
                                  <Tag key={tag}>{tag}</Tag>
                                ))}
                              </div>
                            </>
                          }
                        />
                      </List.Item>
                    )}
                    locale={{ emptyText: <Empty description="暂无文章" /> }}
                  />
                </Card>
              ),
            },
            {
              key: 'cases',
              label: <span><CodeOutlined /> 策略案例</span>,
              children: (
                <Card>
                  <List
                    dataSource={cases}
                    renderItem={(item: Article) => (
                      <List.Item
                        style={{ cursor: 'pointer' }}
                        onClick={() => fetchArticleDetail(item.id)}
                      >
                        <List.Item.Meta
                          title={item.title}
                          description={item.summary}
                        />
                      </List.Item>
                    )}
                    locale={{ emptyText: <Empty description="暂无案例" /> }}
                  />
                </Card>
              ),
            },
            {
              key: 'api',
              label: <span><ApiOutlined /> API文档</span>,
              children: (
                <Card>
                  <Title level={4}>API 接口文档</Title>
                  <Paragraph>
                    完整的 API 文档请访问{' '}
                    <a href="/docs" target="_blank">Swagger UI (/docs)</a>
                    {' '}查看交互式文档。
                  </Paragraph>
                  <Divider />
                  <Title level={5}>快速参考</Title>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#fafafa' }}>
                        <th style={thStyle}>方法</th>
                        <th style={thStyle}>路径</th>
                        <th style={thStyle}>说明</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr><td style={tdStyle}><Tag color="green">POST</Tag></td><td style={tdStyle}>/api/v1/auth/register</td><td style={tdStyle}>用户注册</td></tr>
                      <tr><td style={tdStyle}><Tag color="green">POST</Tag></td><td style={tdStyle}>/api/v1/auth/login</td><td style={tdStyle}>用户登录</td></tr>
                      <tr><td style={tdStyle}><Tag color="blue">GET</Tag></td><td style={tdStyle}>/api/v1/stocks/{"{code}"}/kline</td><td style={tdStyle}>获取K线数据</td></tr>
                      <tr><td style={tdStyle}><Tag color="blue">GET</Tag></td><td style={tdStyle}>/api/v1/market/indices</td><td style={tdStyle}>获取主要指数</td></tr>
                      <tr><td style={tdStyle}><Tag color="green">POST</Tag></td><td style={tdStyle}>/api/v1/simulation/orders</td><td style={tdStyle}>下单</td></tr>
                      <tr><td style={tdStyle}><Tag color="blue">GET</Tag></td><td style={tdStyle}>/api/v1/simulation/positions</td><td style={tdStyle}>查询持仓</td></tr>
                      <tr><td style={tdStyle}><Tag color="green">POST</Tag></td><td style={tdStyle}>/api/v1/backtest/tasks</td><td style={tdStyle}>提交回测任务</td></tr>
                      <tr><td style={tdStyle}><Tag color="blue">GET</Tag></td><td style={tdStyle}>/api/v1/factors</td><td style={tdStyle}>因子列表</td></tr>
                    </tbody>
                  </table>
                </Card>
              ),
            },
          ]}
        />
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = { padding: '8px 12px', textAlign: 'left', borderBottom: '2px solid #e8e8e8' };
const tdStyle: React.CSSProperties = { padding: '8px 12px', borderBottom: '1px solid #f0f0f0' };
