import { useState } from "react";
import { Layout, Menu, Button, Dropdown, Space, Typography } from "antd";
import {
  DashboardOutlined,
  FundOutlined,
  GiftOutlined,
  UserOutlined,
  BarChartOutlined,
  AuditOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const { Header, Sider, Content } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
    { key: "/campaigns", icon: <FundOutlined />, label: "Campaigns" },
    { key: "/bonuses", icon: <GiftOutlined />, label: "Bonus Monitor" },
    { key: "/accounts", icon: <UserOutlined />, label: "Account Lookup" },
    { key: "/reports", icon: <BarChartOutlined />, label: "Reports" },
    { key: "/audit", icon: <AuditOutlined />, label: "Audit Log" },
  ];

  const userMenu = {
    items: [
      { key: "role", label: `Role: ${user?.role?.replace("_", " ")}`, disabled: true },
      { type: "divider" as const },
      { key: "logout", label: "Logout", icon: <LogoutOutlined />, danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === "logout") {
        logout();
        navigate("/login");
      }
    },
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider trigger={null} collapsible collapsed={collapsed} theme="dark">
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography.Title level={4} style={{ color: "#fff", margin: 0 }}>
            {collapsed ? "MT5" : "MT5 Bonus"}
          </Typography.Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: "0 24px", background: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown menu={userMenu}>
            <Space style={{ cursor: "pointer" }}>
              <UserOutlined />
              {user?.full_name}
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: "#fff", borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
