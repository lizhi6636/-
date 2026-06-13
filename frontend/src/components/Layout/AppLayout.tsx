import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Layout, Drawer, Button, theme } from 'antd';
import { MenuOutlined } from '@ant-design/icons';
import SideMenu from './SideMenu';
import HeaderBar from './HeaderBar';
import ErrorBoundary from '../common/ErrorBoundary';

const { Content, Sider } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const { token } = theme.useToken();

  useEffect(() => {
    const onResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) setMobileMenuOpen(false);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const sidebarContent = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 20,
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          whiteSpace: 'nowrap',
          flexShrink: 0,
        }}
      >
        量化学习平台
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <SideMenu onClick={() => setMobileMenuOpen(false)} />
      </div>
    </div>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 桌面端：固定侧边栏 */}
      {!isMobile && (
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
          {sidebarContent}
        </Sider>
      )}

      {/* 手机端：抽屉菜单 */}
      {isMobile && (
        <Drawer
          placement="left"
          open={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          width={220}
          styles={{ body: { padding: 0, background: token.colorBgElevated } }}
          closeIcon={null}
        >
          <div style={{ background: '#001529', height: '100%' }}>
            {sidebarContent}
          </div>
        </Drawer>
      )}

      <Layout style={{
        marginLeft: isMobile ? 0 : (collapsed ? 80 : 220),
        transition: 'margin-left 0.2s',
      }}>
        <HeaderBar
          isMobile={isMobile}
          onMenuClick={() => setMobileMenuOpen(true)}
        />
        <Content style={{
          margin: isMobile ? 8 : 16,
          minHeight: 'calc(100vh - 96px)',
        }}>
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </Content>
      </Layout>
    </Layout>
  );
}
