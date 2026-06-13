import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Checkbox, Typography, message, Alert } from 'antd';
import { MailOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authSlice';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const onFinish = async (values: { email: string; password: string; remember_me: boolean }) => {
    setError('');
    setLoading(true);
    try {
      await login({ email: values.email, password: values.password, remember_me: values.remember_me });
      message.success('登录成功！');
      navigate('/', { replace: true });
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || '登录失败';
      setError(typeof detail === 'string' ? detail : '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card style={{ width: 400, borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ marginBottom: 4 }}>量化学习平台</Title>
          <Text type="secondary">登录您的账户</Text>
        </div>

        {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

        <Form layout="vertical" onFinish={onFinish} size="large" requiredMark={false}
          initialValues={{ remember_me: true }}>
          <Form.Item name="email" rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效邮箱' },
          ]}>
            <Input prefix={<MailOutlined />} placeholder="邮箱地址" />
          </Form.Item>

          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item name="remember_me" valuePropName="checked">
            <Checkbox>记住登录（30天内无需重新登录）</Checkbox>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              {loading ? '登录中...' : '登录'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center' }}>
          <Text>还没有账户？</Text> <Link to="/register">立即注册</Link>
        </div>
      </Card>
    </div>
  );
}
