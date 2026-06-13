import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Tag, message, Tabs, Input, Modal, Form,
  Select, Space, Typography, Spin,
} from 'antd';
import { PlusOutlined, DeleteOutlined, ExperimentOutlined } from '@ant-design/icons';
import { factorApi } from '../../api/factor';
import type { FactorDefinition } from '../../types/factor';

const { TextArea } = Input;
const { Text } = Typography;

export default function FactorPage() {
  const [factors, setFactors] = useState<FactorDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchFactors = async () => {
    try {
      const res = await factorApi.listFactors();
      setFactors(res.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchFactors(); }, []);

  const handleCreate = async (values: any) => {
    try {
      await factorApi.createFactor(values);
      message.success('因子创建成功！');
      setModalOpen(false);
      form.resetFields();
      fetchFactors();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '创建失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await factorApi.deleteFactor(id);
      message.success('已删除');
      fetchFactors();
    } catch { message.error('删除失败'); }
  };

  const handlePreview = async (expression: string) => {
    try {
      const res = await factorApi.previewFactor({
        expression,
        stock_code: '000001',
        start_date: '20250101',
        end_date: '20250601',
      });
      message.info(`最新值: ${res.data.latest_value ?? '计算失败'}`);
    } catch { message.error('预览失败'); }
  };

  const categoryColors: Record<string, string> = {
    system: 'blue', custom: 'green', technical: 'orange', fundamental: 'purple',
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <Card
        title="因子库"
        size="small"
        extra={
          <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            新建因子
          </Button>
        }
      >
        <Table
          dataSource={factors}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 15 }}
          columns={[
            { title: '名称', dataIndex: 'display_name', width: 180 },
            { title: '标识', dataIndex: 'name', width: 120 },
            { title: '描述', dataIndex: 'description', width: 200, ellipsis: true },
            { title: '表达式', dataIndex: 'expression', width: 200, ellipsis: true,
              render: (v: string) => <Text code>{v}</Text>,
            },
            {
              title: '类别', dataIndex: 'category', width: 90,
              render: (v: string) => <Tag color={categoryColors[v]}>{v}</Tag>,
            },
            {
              title: '操作', width: 160,
              render: (_: any, record: FactorDefinition) => (
                <Space>
                  <Button size="small" icon={<ExperimentOutlined />}
                    onClick={() => handlePreview(record.expression)}>
                    预览
                  </Button>
                  {record.category !== 'system' && (
                    <Button size="small" danger icon={<DeleteOutlined />}
                      onClick={() => handleDelete(record.id)} />
                  )}
                </Space>
              ),
            },
          ]}
          locale={{ emptyText: '暂无因子' }}
        />
      </Card>

      <Modal
        title="新建自定义因子"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form layout="vertical" form={form} onFinish={handleCreate}>
          <Form.Item name="name" label="因子标识" rules={[{ required: true }]}>
            <Input placeholder="如: my_factor" />
          </Form.Item>
          <Form.Item name="display_name" label="显示名称" rules={[{ required: true }]}>
            <Input placeholder="如: 我的自定义因子" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input placeholder="因子说明" />
          </Form.Item>
          <Form.Item name="expression" label="计算表达式" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="如: (close - close_20d_ago) / close_20d_ago" />
          </Form.Item>
          <Form.Item name="category" label="类别" initialValue="custom">
            <Select options={[
              { value: 'custom', label: '自定义' },
              { value: 'technical', label: '技术因子' },
              { value: 'fundamental', label: '基本面因子' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
