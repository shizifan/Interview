import { Layout, Menu, Button } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  SettingOutlined,
  TrophyOutlined,
  SolutionOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/hr', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/hr/jobs', icon: <FileTextOutlined />, label: '岗位管理' },
  { key: '/hr/candidates', icon: <TeamOutlined />, label: '候选人管理' },
  { key: '/hr/interviews', icon: <SolutionOutlined />, label: '面试记录' },
  { key: '/hr/score-pool', icon: <TrophyOutlined />, label: '评分池' },
  { key: '/hr/settings', icon: <SettingOutlined />, label: '系统设置' },
];

export default function HRLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);

  const selectedKey = menuItems.find((item) =>
    location.pathname === item.key || (item.key !== '/hr' && location.pathname.startsWith(item.key))
  )?.key || '/hr';

  const handleLogout = () => {
    logout();
    navigate('/hr/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <span style={{ fontSize: 18, fontWeight: 600, color: '#1677ff' }}>AI面试官 · HR</span>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderInlineEnd: 'none' }}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 16, fontWeight: 500 }}>
            {menuItems.find((i) => i.key === selectedKey)?.label || '管理后台'}
          </span>
          <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>
            退出登录
          </Button>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
