import { useEffect, useState } from "react";
import { Descriptions, Tag, Button, Space, Typography, Card, Spin, message } from "antd";
import { useParams, useNavigate } from "react-router-dom";
import { getCampaign, updateCampaignStatus } from "../../api/endpoints";
import type { Campaign, CampaignStatus } from "../../types";
import dayjs from "dayjs";

const statusColors: Record<CampaignStatus, string> = {
  draft: "default", active: "green", paused: "orange", ended: "red", archived: "gray",
};

const bonusTypeLabels: Record<string, string> = {
  A: "Type A - Dynamic Leverage", B: "Type B - Fixed Leverage", C: "Type C - Convertible",
};

export default function CampaignDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    getCampaign(Number(id)).then((res) => setCampaign(res.data)).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [id]);

  const handleStatus = async (status: string) => {
    await updateCampaignStatus(Number(id), status);
    message.success("Status updated");
    fetchData();
  };

  if (loading || !campaign) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>{campaign.name}</Typography.Title>
        <Space>
          {campaign.status === "draft" && <Button type="primary" onClick={() => handleStatus("active")}>Activate</Button>}
          {campaign.status === "active" && <Button onClick={() => handleStatus("paused")}>Pause</Button>}
          {campaign.status === "paused" && <Button type="primary" onClick={() => handleStatus("active")}>Resume</Button>}
          {campaign.status !== "archived" && <Button danger onClick={() => handleStatus("archived")}>Archive</Button>}
          <Button onClick={() => navigate(`/campaigns/${id}/edit`)}>Edit</Button>
          <Button onClick={() => navigate("/campaigns")}>Back</Button>
        </Space>
      </div>
      <Card>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Status"><Tag color={statusColors[campaign.status]}>{campaign.status.toUpperCase()}</Tag></Descriptions.Item>
          <Descriptions.Item label="Bonus Type">{bonusTypeLabels[campaign.bonus_type]}</Descriptions.Item>
          <Descriptions.Item label="Bonus %">{campaign.bonus_percentage}%</Descriptions.Item>
          <Descriptions.Item label="Max Bonus">{campaign.max_bonus_amount ? `$${campaign.max_bonus_amount}` : "No limit"}</Descriptions.Item>
          <Descriptions.Item label="Min Deposit">{campaign.min_deposit ? `$${campaign.min_deposit}` : "None"}</Descriptions.Item>
          <Descriptions.Item label="Max Deposit">{campaign.max_deposit ? `$${campaign.max_deposit}` : "None"}</Descriptions.Item>
          <Descriptions.Item label="Triggers">{campaign.trigger_types.join(", ") || "None"}</Descriptions.Item>
          <Descriptions.Item label="Promo Code">{campaign.promo_code || "N/A"}</Descriptions.Item>
          {campaign.bonus_type === "C" && (
            <>
              <Descriptions.Item label="Lot Requirement">{campaign.lot_requirement}</Descriptions.Item>
              <Descriptions.Item label="Lot Tracking">{campaign.lot_tracking_scope || "all"}</Descriptions.Item>
            </>
          )}
          <Descriptions.Item label="Expiry">{campaign.expiry_days ? `${campaign.expiry_days} days` : "No expiry"}</Descriptions.Item>
          <Descriptions.Item label="One Per Account">{campaign.one_bonus_per_account ? "Yes" : "No"}</Descriptions.Item>
          <Descriptions.Item label="Max Concurrent">{campaign.max_concurrent_bonuses}</Descriptions.Item>
          <Descriptions.Item label="Active Bonuses">{campaign.active_bonus_count ?? 0}</Descriptions.Item>
          <Descriptions.Item label="Target Groups">{campaign.target_mt5_groups?.join(", ") || "All"}</Descriptions.Item>
          <Descriptions.Item label="Start">{campaign.start_date ? dayjs(campaign.start_date).format("YYYY-MM-DD HH:mm") : "Immediate"}</Descriptions.Item>
          <Descriptions.Item label="End">{campaign.end_date ? dayjs(campaign.end_date).format("YYYY-MM-DD HH:mm") : "No end date"}</Descriptions.Item>
          <Descriptions.Item label="Created">{dayjs(campaign.created_at).format("YYYY-MM-DD HH:mm")}</Descriptions.Item>
          <Descriptions.Item label="Notes" span={2}>{campaign.notes || "None"}</Descriptions.Item>
        </Descriptions>
      </Card>
    </>
  );
}
