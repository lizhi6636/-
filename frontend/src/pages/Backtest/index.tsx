import { useState, useEffect, useCallback } from 'react';
import {
  Row, Col, Card, Form, Input, Button, DatePicker, InputNumber,
  Table, Tag, Spin, message, Typography, Statistic, Space,
} from 'antd';
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { backtestApi } from '../../api/backtest';
import type { BacktestTask } from '../../types/backtest';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { RangePicker } = DatePicker;
const { Text } = Typography;

const DEFAULT_STRATEGY = `import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ('fast', 10),
        ('slow', 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(
            self.data.close, period=self.params.fast
        )
        self.slow_ma = bt.indicators.SMA(
            self.data.close, period=self.params.slow
        )
        self.crossover = bt.indicators.CrossOver(
            self.fast_ma, self.slow_ma
        )

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.sell()
`;

export default function BacktestPage() {
  const [tasks, setTasks] = useState<BacktestTask[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [pollingId, setPollingId] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await backtestApi.getTasks();
      setTasks(res.data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  // Poll running tasks
  useEffect(() => {
    const runningTask = tasks.find((t) => t.status === 'running');
    if (runningTask) {
      setPollingId(runningTask.id);
      const interval = setInterval(async () => {
        try {
          const res = await backtestApi.getTask(runningTask.id);
          if (res.data.status !== 'running') {
            clearInterval(interval);
            setPollingId(null);
            fetchTasks();
          }
        } catch { clearInterval(interval); }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [tasks, fetchTasks]);

  const handleSubmit = async (values: any) => {
    setSubmitting(true);
    try {
      await backtestApi.createTask({
        name: values.name || '未命名策略',
        strategy_code: values.strategy_code,
        stock_codes: values.stock_codes.split(/[,，\s]+/).filter(Boolean),
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
        initial_capital: (values.initial_capital || 1000000).toString(),
        parameters: {},
      });
      message.success('回测任务已提交！');
      fetchTasks();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        {/* Strategy Config */}
        <Col xs={24} lg={10}>
          <Card title="策略配置" size="small">
            <Form layout="vertical" onFinish={handleSubmit} size="small"
              initialValues={{
                strategy_code: DEFAULT_STRATEGY,
                initial_capital: 1000000,
              }}
            >
              <Form.Item name="name" label="策略名称">
                <Input placeholder="双均线策略" />
              </Form.Item>
              <Form.Item name="stock_codes" label="股票代码" rules={[{ required: true, message: '请输入至少一个股票代码' }]}>
                <Input placeholder="000001, 600000, 399006" />
              </Form.Item>
              <Form.Item name="date_range" label="回测区间" rules={[{ required: true }]}>
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="initial_capital" label="初始资金">
                <InputNumber style={{ width: '100%' }} min={10000} step={100000} />
              </Form.Item>
              <Form.Item name="strategy_code" label="策略代码" rules={[{ required: true }]}>
                <TextArea rows={12} style={{ fontFamily: 'monospace', fontSize: 12 }} />
              </Form.Item>
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={submitting}
                  icon={<PlayCircleOutlined />}
                  block
                >
                  运行回测
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Results */}
        <Col xs={24} lg={14}>
          <Card
            title="回测历史"
            size="small"
            extra={<Button size="small" icon={<ReloadOutlined />} onClick={fetchTasks}>刷新</Button>}
          >
            <Table
              dataSource={tasks}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 10 }}
              columns={[
                { title: '名称', dataIndex: 'name', width: 120 },
                { title: '股票', dataIndex: 'stock_codes', width: 150,
                  render: (v: string[]) => v?.join(', '),
                },
                {
                  title: '状态', dataIndex: 'status', width: 90,
                  render: (v: string) => {
                    const colors: Record<string, string> = {
                      pending: 'blue', running: 'orange', completed: 'green', failed: 'red',
                    };
                    return <Tag color={colors[v]}>{v}</Tag>;
                  },
                },
                {
                  title: '收益率', width: 90,
                  render: (_: any, record: BacktestTask) =>
                    record.metrics
                      ? <Text type={Number((record.metrics as Record<string,any>).total_return) >= 0 ? 'danger' : 'success'}>
                          {(record.metrics as Record<string,any>).total_return}%
                        </Text>
                      : '-',
                },
                {
                  title: '夏普', width: 80,
                  render: (_: any, record: BacktestTask) =>
                    (record.metrics as any)?.sharpe_ratio ?? '-',
                },
                {
                  title: '最大回撤', width: 90,
                  render: (_: any, record: BacktestTask) =>
                    (record.metrics as any)?.max_drawdown != null
                      ? `${(record.metrics as any).max_drawdown}%`
                      : '-',
                },
                { title: '创建时间', dataIndex: 'created_at', width: 150,
                  render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
                },
              ]}
              locale={{ emptyText: '暂无回测任务，请提交一个策略' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
