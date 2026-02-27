import { useEffect, useState } from "react";
import { Table, Button, Tag, Space, Typography, Input, Select, message } from "antd";
import { PlusOutlined, CopyOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getCampaigns, updateCampaignStatus, duplicateCampaign } from "../../api/endpoints";
import type { CampaignListItem, CampaignStatus } from "../../types";
import dayjs from "dayjs";

const statusColors: Record<CampaignStatus, string> = {
  draft: "default",
  active: "green",
  paused: "orange",
  ended: "red",
  archived: "gray",
};

const bonusTypeLabels: Record<string, string> = {
  A: "Dynamic Leverage",
  B: "Fixed Leverage",
  C: "Convertible",
};

export default function CampaignList() {
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 25 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await getCampaigns(params);
      setCampaigns(res.data.items);
      setTotal(res.data.total);
    } catch {
      message.error("Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, statusFilter]);

  const handleStatusChange = async (id: number, newStatus: string) => {
    await updateCampaignStatus(id, newStatus);
    message.success("Status updated");
    fetchData();
  };

  const handleDuplicate = async (id: number) => {
    await duplicateCampaign(id);
    message.success("Campaign duplicated");
    fetchData();
  };

  const columns = [
    { title: "Name", dataIndex: "name", key: "name", render: (text: string, r: CampaignListItem) => <a onClick={() => navigate(`/campaigns/${r.id}`)}>{text}</a> },
    { title: "Status", dataIndex: "status", key: "status", render: (s: CampaignStatus) => <Tag color={statusColors[s]}>{s.toUpperCase()}</Tag> },
    { title: "Type", dataIndex: "bonus_type", key: "bonus_type", render: (t: string) => bonusTypeLabels[t] || t },
    { title: "Bonus %", dataIndex: "bonus_percentage", key: "bonus_percentage", render: (v: number) => `${v}%` },
    { title: "Active Bonuses", dataIndex: "active_bonus_count", key: "active_bonus_count" },
    { title: "Created", dataIndex: "created_at", key: "created_at", render: (d: string) => dayjs(d).format("YYYY-MM-DD") },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, r: CampaignListItem) => (
        <Space>
          {r.status === "draft" && <Button size="small" type="primary" onClick={() => handleStatusChange(r.id, "active")}>Activate</Button>}
          {r.status === "active" && <Button size="small" onClick={() => handleStatusChange(r.id, "paused")}>Pause</Button>}
          {r.status === "paused" && <Button size="small" type="primary" onClick={() => handleStatusChange(r.id, "active")}>Resume</Button>}
          <Button size="small" icon={<CopyOutlined />} onClick={() => handleDuplicate(r.id)} />
        </Space>
      ),
    },
  ];

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>Campaigns</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/campaigns/new")}>
          New Campaign
        </Button>
      </div>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search placeholder="Search campaigns" onSearch={(v) => { setSearch(v); setPage(1); fetchData(); }} style={{ width: 250 }} allowClear />
        <Select placeholder="Status" allowClear style={{ width: 150 }} onChange={(v) => { setStatusFilter(v || ""); setPage(1); }}
          options={[
            { label: "Active", value: "active" },
            { label: "Draft", value: "draft" },
            { label: "Paused", value: "paused" },
            { label: "Ended", value: "ended" },
            { label: "Archived", value: "archived" },
          ]}
        />
      </Space>
      <Table
        columns={columns}
        dataSource={campaigns}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 25, onChange: setPage }}
      />
    </>
  );
}
