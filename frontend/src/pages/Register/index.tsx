import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message, Alert } from 'antd';
import { MailOutlined, LockOutlined, UserOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authSlice';

const { Title, Text } = Typography;

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const register = useAuthStore((s) => s.register);
  const navigate = useNavigate();

  const onFinish = async (values: { email: string; username: string; password: string; confirmPassword: string }) => {
    setError('');
    if (values.password !== values.confirmPassword) {
      setError('两次密码不一致');
      return;
    }
    setLoading(true);
    try {
      await register({ email: values.email, username: values.username, password: values.password });
      message.success('注册成功！初始资金100万，请登录');
      navigate('/login');
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || '注册失败，请稍后重试';
      setError(typeof detail === 'string' ? detail : '注册失败');
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
          <Title level={2} style={{ marginBottom: 4 }}>创建账户</Title>
          <Text type="secondary">注册即获得100万模拟资金</Text>
        </div>

        {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

        <Form layout="vertical" onFinish={onFinish} size="large" requiredMark={false}>
          <Form.Item name="email" rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效邮箱格式' },
          ]}>
            <Input prefix={<MailOutlined />} placeholder="邮箱地址" />
          </Form.Item>

          <Form.Item name="username" rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少3个字符' },
            { max: 50, message: '用户名最多50个字符' },
            { pattern: /^[a-zA-Z0-9_\-一-龥]+$/, message: '用户名只能包含中英文、数字、下划线和连字符' },
          ]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item name="password" rules={[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少6个字符' },
          ]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少6位）" />
          </Form.Item>

          <Form.Item name="confirmPassword" rules={[
            { required: true, message: '请再次输入密码' },
          ]}>
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              {loading ? '注册中...' : '注册'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center' }}>
          <Text>已有账户？</Text> <Link to="/login">立即登录</Link>
        </div>
      </Card>
    </div>
  );
}
