import { useNavigate, useLocation } from 'react-router-dom';
import { Menu } from 'antd';
import {
  DashboardOutlined,
  LineChartOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  DollarOutlined,
  ReadOutlined,
} from '@ant-design/icons';

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/simulation', icon: <DollarOutlined />, label: '模拟交易' },
  { key: '/backtest', icon: <ExperimentOutlined />, label: '回测工作台' },
  { key: '/factor', icon: <BarChartOutlined />, label: '因子挖掘' },
  { key: '/learn', icon: <ReadOutlined />, label: '量化学院' },
];

export default function SideMenu() {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = '/' + location.pathname.split('/')[1];

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[selectedKey === '/' ? '/' : selectedKey]}
      items={menuItems}
      onClick={({ key }) => navigate(key)}
      style={{ marginTop: 8 }}
    />
  );
}
