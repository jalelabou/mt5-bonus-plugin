import { useEffect, useState } from "react";
import { Table, Tag, Space, Typography, Select, Input, Button, Modal, message, Progress, Descriptions, InputNumber, Spin } from "antd";
import { getBonuses, cancelBonus, forceConvert, assignBonus, getCampaigns, getMT5Metadata, getAccount } from "../../api/endpoints";
import type { Bonus, BonusStatusType } from "../../types";
import dayjs from "dayjs";

interface MT5AccountOption {
  login: string;
  name: string;
  group: string;
  country: string;
}

interface AccountDetail {
  login: string;
  name: string;
  balance: number;
  equity: number;
  credit: number;
  leverage: number;
  group: string;
  country: string;
}

const statusColors: Record<BonusStatusType, string> = {
  active: "green", converted: "blue", cancelled: "red", expired: "gray",
};

export default function BonusMonitor() {
  const [bonuses, setBonuses] = useState<Bonus[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loginFilter, setLoginFilter] = useState("");
  const [assignModal, setAssignModal] = useState(false);
  const [assignData, setAssignData] = useState({ campaign_id: 0, mt5_login: "", deposit_amount: 0 });
  const [campaignOptions, setCampaignOptions] = useState<{ label: string; value: number }[]>([]);
  const [mt5Accounts, setMt5Accounts] = useState<MT5AccountOption[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<AccountDetail | null>(null);
  const [loadingAccount, setLoadingAccount] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 25 };
      if (statusFilter) params.status = statusFilter;
      if (loginFilter) params.mt5_login = loginFilter;
      const res = await getBonuses(params);
      setBonuses(res.data.items);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, statusFilter]);

  const handleCancel = async (id: number) => {
    await cancelBonus(id, "admin_cancel");
    message.success("Bonus cancelled");
    fetchData();
  };

  const handleForceConvert = async (id: number) => {
    await forceConvert(id);
    message.success("Bonus force converted");
    fetchData();
  };

  const openAssignModal = async () => {
    setAssignData({ campaign_id: 0, mt5_login: "", deposit_amount: 0 });
    setSelectedAccount(null);
    const [campaignRes, metaRes] = await Promise.all([
      getCampaigns({ status: "active", page_size: 100 }),
      getMT5Metadata(),
    ]);
    setCampaignOptions(campaignRes.data.items.map((c) => ({ label: `${c.name} (${c.bonus_type === "A" ? "Dynamic" : c.bonus_type === "B" ? "Fixed" : "Convertible"} ${c.bonus_percentage}%)`, value: c.id })));
    setMt5Accounts(metaRes.data.accounts || []);
    setAssignModal(true);
  };

  const handleAccountSelect = async (login: string) => {
    setAssignData((prev) => ({ ...prev, mt5_login: login }));
    setLoadingAccount(true);
    try {
      const res = await getAccount(login);
      const acct = res.data.account as AccountDetail;
      setSelectedAccount(acct);
      setAssignData((prev) => ({ ...prev, mt5_login: login, deposit_amount: acct.balance }));
    } catch {
      setSelectedAccount(null);
    } finally {
      setLoadingAccount(false);
    }
  };

  const handleAssign = async () => {
    if (!assignData.campaign_id) { message.error("Select a campaign"); return; }
    if (!assignData.mt5_login) { message.error("Select an account"); return; }
    try {
      await assignBonus(assignData);
      message.success("Bonus assigned");
      setAssignModal(false);
      setSelectedAccount(null);
      fetchData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "Failed to assign");
    }
  };

  const columns = [
    { title: "Account", dataIndex: "mt5_login", key: "mt5_login" },
    { title: "Campaign", dataIndex: "campaign_name", key: "campaign_name" },
    { title: "Type", dataIndex: "bonus_type", key: "bonus_type", render: (t: string) => ({ A: "Dynamic", B: "Fixed", C: "Convertible" })[t] },
    { title: "Amount", dataIndex: "bonus_amount", key: "bonus_amount", render: (v: number) => `$${v.toFixed(2)}` },
    {
      title: "Progress", key: "progress",
      render: (_: unknown, r: Bonus) => r.bonus_type === "C" && r.lots_required ? (
        <Space direction="vertical" size={0}>
          <Progress percent={r.percent_converted || 0} size="small" style={{ width: 120 }} />
          <small>{r.lots_traded}/{r.lots_required} lots</small>
        </Space>
      ) : "-",
    },
    { title: "Status", dataIndex: "status", key: "status", render: (s: BonusStatusType) => <Tag color={statusColors[s]}>{s.toUpperCase()}</Tag> },
    { title: "Assigned", dataIndex: "assigned_at", key: "assigned_at", render: (d: string) => dayjs(d).format("YYYY-MM-DD HH:mm") },
    { title: "Expires", dataIndex: "expires_at", key: "expires_at", render: (d: string | null) => d ? dayjs(d).format("YYYY-MM-DD") : "-" },
    {
      title: "Actions", key: "actions",
      render: (_: unknown, r: Bonus) => r.status === "active" ? (
        <Space>
          <Button size="small" danger onClick={() => handleCancel(r.id)}>Cancel</Button>
          {r.bonus_type === "C" && <Button size="small" onClick={() => handleForceConvert(r.id)}>Force Convert</Button>}
        </Space>
      ) : null,
    },
  ];

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>Bonus Monitor</Typography.Title>
        <Button type="primary" onClick={openAssignModal}>Assign Bonus</Button>
      </div>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search placeholder="MT5 Login" onSearch={(v) => { setLoginFilter(v); setPage(1); fetchData(); }} style={{ width: 200 }} allowClear />
        <Select placeholder="Status" allowClear style={{ width: 150 }} onChange={(v) => { setStatusFilter(v || ""); setPage(1); }}
          options={[
            { label: "Active", value: "active" },
            { label: "Converted", value: "converted" },
            { label: "Cancelled", value: "cancelled" },
            { label: "Expired", value: "expired" },
          ]}
        />
      </Space>
      <Table columns={columns} dataSource={bonuses} rowKey="id" loading={loading} pagination={{ current: page, total, pageSize: 25, onChange: setPage }} />

      <Modal title="Assign Bonus" open={assignModal} onOk={handleAssign} onCancel={() => { setAssignModal(false); setSelectedAccount(null); }} width={600}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <div>
            <Typography.Text strong style={{ display: "block", marginBottom: 4 }}>MT5 Account</Typography.Text>
            <Select
              showSearch
              placeholder="Search by login or name..."
              style={{ width: "100%" }}
              value={assignData.mt5_login || undefined}
              onChange={handleAccountSelect}
              filterOption={(input, option) => {
                const label = (option?.label ?? "").toString().toLowerCase();
                return label.includes(input.toLowerCase());
              }}
              options={mt5Accounts.map((a) => ({
                label: `${a.login} — ${a.name} (${a.group}, ${a.country})`,
                value: a.login,
              }))}
            />
          </div>

          {loadingAccount && <Spin size="small" />}

          {selectedAccount && (
            <Descriptions size="small" bordered column={2} style={{ marginBottom: 0 }}>
              <Descriptions.Item label="Login">{selectedAccount.login}</Descriptions.Item>
              <Descriptions.Item label="Name">{selectedAccount.name}</Descriptions.Item>
              <Descriptions.Item label="Balance">${selectedAccount.balance.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="Equity">${selectedAccount.equity.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="Credit">${selectedAccount.credit.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="Leverage">1:{selectedAccount.leverage}</Descriptions.Item>
              <Descriptions.Item label="Group" span={2}>{selectedAccount.group}</Descriptions.Item>
            </Descriptions>
          )}

          <div>
            <Typography.Text strong style={{ display: "block", marginBottom: 4 }}>Campaign</Typography.Text>
            <Select placeholder="Select campaign" style={{ width: "100%" }} options={campaignOptions} onChange={(v) => setAssignData((prev) => ({ ...prev, campaign_id: v }))} />
          </div>

          <div>
            <Typography.Text strong style={{ display: "block", marginBottom: 4 }}>Deposit Amount</Typography.Text>
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              value={assignData.deposit_amount}
              onChange={(v) => setAssignData((prev) => ({ ...prev, deposit_amount: v || 0 }))}
              addonBefore="$"
            />
          </div>
        </Space>
      </Modal>
    </>
  );
}
