import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Typography, Spin } from "antd";
import { FundOutlined, GiftOutlined, DollarOutlined, SwapOutlined } from "@ant-design/icons";
import { getCampaigns, getBonuses } from "../api/endpoints";

export default function Dashboard() {
  const [stats, setStats] = useState({ campaigns: 0, activeBonuses: 0, totalAmount: 0, convertedCount: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCampaigns({ status: "active", page_size: 1 }),
      getBonuses({ status: "active", page_size: 1 }),
      getBonuses({ status: "converted", page_size: 1 }),
    ])
      .then(([campRes, bonusRes, convertedRes]) => {
        setStats({
          campaigns: campRes.data.total,
          activeBonuses: bonusRes.data.total,
          totalAmount: 0,
          convertedCount: convertedRes.data.total,
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Active Campaigns" value={stats.campaigns} prefix={<FundOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Active Bonuses" value={stats.activeBonuses} prefix={<GiftOutlined />} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Converted Bonuses" value={stats.convertedCount} prefix={<SwapOutlined />} valueStyle={{ color: "#1677ff" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="System Status" value="Online" prefix={<DollarOutlined />} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
      </Row>
    </>
  );
}
