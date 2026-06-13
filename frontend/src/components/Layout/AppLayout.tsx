import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Layout } from 'antd';
import SideMenu from './SideMenu';
import HeaderBar from './HeaderBar';
import ErrorBoundary from '../common/ErrorBoundary';

const { Content, Sider } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 10,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 20,
            fontWeight: 'bold',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            whiteSpace: 'nowrap',
          }}
        >
          {collapsed ? 'QL' : '量化学习平台'}
        </div>
        <SideMenu />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin-left 0.2s' }}>
        <HeaderBar />
        <Content style={{ margin: 16, minHeight: 'calc(100vh - 96px)' }}>
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </Content>
      </Layout>
    </Layout>
  );
}
