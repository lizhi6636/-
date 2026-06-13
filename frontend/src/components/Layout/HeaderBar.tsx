import { useEffect } from 'react';
import { Layout, Space, Badge, Dropdown, Avatar, Typography } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authSlice';
import { useClockStore } from '../../store/clockSlice';
import { dashboardApi } from '../../api/dashboard';

const { Header } = Layout;
const { Text } = Typography;

export default function HeaderBar() {
  const { user, logout } = useAuthStore();
  const { status, setStatus } = useClockStore();

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await dashboardApi.getTradingStatus();
        setStatus(res.data);
      } catch {
        // ignore
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, [setStatus]);

  const tradingColor = status?.is_trading ? '#52c41a' : '#faad14';

  return (
    <Header
      style={{
        background: '#fff',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        height: 56,
      }}
    >
      <Space>
        <Badge
          status={status?.is_trading ? 'processing' : 'default'}
          color={tradingColor}
          text={
            <Text style={{ fontSize: 13 }}>
              {status?.message || '加载中...'}
            </Text>
          }
        />
      </Space>

      <Dropdown
        menu={{
          items: [
            {
              key: 'logout',
              icon: <LogoutOutlined />,
              label: '退出登录',
              danger: true,
              onClick: logout,
            },
          ],
        }}
      >
        <Space style={{ cursor: 'pointer' }}>
          <Avatar size="small" icon={<UserOutlined />} />
          <Text>{user?.username || '用户'}</Text>
        </Space>
      </Dropdown>
    </Header>
  );
}
