import { useState } from "react";
import { Input, Card, Descriptions, Table, Tag, Typography, Spin, message, Tabs } from "antd";
import { getAccount } from "../../api/endpoints";
import type { MT5Account, Bonus, AuditLogEntry, BonusStatusType } from "../../types";
import dayjs from "dayjs";

const statusColors: Record<BonusStatusType, string> = {
  active: "green", converted: "blue", cancelled: "red", expired: "gray",
};

export default function AccountLookup() {
  const [account, setAccount] = useState<MT5Account | null>(null);
  const [bonuses, setBonuses] = useState<Bonus[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (login: string) => {
    if (!login.trim()) return;
    setLoading(true);
    try {
      const res = await getAccount(login.trim());
      setAccount(res.data.account);
      setBonuses(res.data.bonuses);
      setAuditLogs(res.data.audit_logs);
    } catch {
      message.error("Account not found");
      setAccount(null);
    } finally {
      setLoading(false);
    }
  };

  const bonusCols = [
    { title: "Campaign", dataIndex: "campaign_name", key: "campaign_name" },
    { title: "Type", dataIndex: "bonus_type", key: "bonus_type" },
    { title: "Amount", dataIndex: "bonus_amount", key: "bonus_amount", render: (v: number) => `$${v.toFixed(2)}` },
    { title: "Status", dataIndex: "status", key: "status", render: (s: BonusStatusType) => <Tag color={statusColors[s]}>{s.toUpperCase()}</Tag> },
    { title: "Assigned", dataIndex: "assigned_at", key: "assigned_at", render: (d: string) => dayjs(d).format("YYYY-MM-DD HH:mm") },
  ];

  const auditCols = [
    { title: "Event", dataIndex: "event_type", key: "event_type", render: (t: string) => <Tag>{t}</Tag> },
    { title: "Actor", dataIndex: "actor_type", key: "actor_type" },
    { title: "Details", key: "details", render: (_: unknown, r: AuditLogEntry) => JSON.stringify(r.after_state || r.before_state || {}).substring(0, 80) },
    { title: "Time", dataIndex: "created_at", key: "created_at", render: (d: string) => dayjs(d).format("YYYY-MM-DD HH:mm:ss") },
  ];

  return (
    <>
      <Typography.Title level={3}>Account Lookup</Typography.Title>
      <Input.Search placeholder="Enter MT5 Login (e.g. 10001)" onSearch={handleSearch} enterButton="Search" size="large" style={{ maxWidth: 500, marginBottom: 24 }} />

      {loading && <Spin size="large" style={{ display: "block", margin: "40px auto" }} />}

      {account && !loading && (
        <>
          <Card style={{ marginBottom: 24 }}>
            <Descriptions title="Account Info" bordered column={3}>
              <Descriptions.Item label="Login">{account.login}</Descriptions.Item>
              <Descriptions.Item label="Name">{account.name}</Descriptions.Item>
              <Descriptions.Item label="Group">{account.group}</Descriptions.Item>
              <Descriptions.Item label="Balance">${account.balance.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="Equity">${account.equity.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="Credit">${account.credit.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="Leverage">1:{account.leverage}</Descriptions.Item>
              <Descriptions.Item label="Country">{account.country}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Tabs items={[
            { key: "bonuses", label: `Bonuses (${bonuses.length})`, children: <Table columns={bonusCols} dataSource={bonuses} rowKey="id" size="small" pagination={false} /> },
            { key: "audit", label: `Audit Log (${auditLogs.length})`, children: <Table columns={auditCols} dataSource={auditLogs} rowKey="id" size="small" pagination={{ pageSize: 20 }} /> },
          ]} />
        </>
      )}
    </>
  );
}
