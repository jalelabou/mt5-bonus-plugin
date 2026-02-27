import { useEffect, useState } from "react";
import { Table, Tag, Typography, Input, Select, Space } from "antd";
import { getAuditLogs } from "../../api/endpoints";
import type { AuditLogEntry, EventType } from "../../types";
import dayjs from "dayjs";

const eventColors: Record<EventType, string> = {
  assignment: "green",
  cancellation: "red",
  conversion_step: "blue",
  leverage_change: "orange",
  expiry: "gray",
  admin_override: "purple",
};

export default function AuditLog() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [loginFilter, setLoginFilter] = useState("");
  const [eventFilter, setEventFilter] = useState<string>("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 50 };
      if (loginFilter) params.mt5_login = loginFilter;
      if (eventFilter) params.event_type = eventFilter;
      const res = await getAuditLogs(params);
      setLogs(res.data.items);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, eventFilter]);

  const columns = [
    { title: "Time", dataIndex: "created_at", key: "created_at", width: 180, render: (d: string) => dayjs(d).format("YYYY-MM-DD HH:mm:ss") },
    { title: "Event", dataIndex: "event_type", key: "event_type", render: (t: EventType) => <Tag color={eventColors[t]}>{t}</Tag> },
    { title: "Actor", dataIndex: "actor_type", key: "actor_type", render: (t: string, r: AuditLogEntry) => `${t}${r.actor_id ? ` #${r.actor_id}` : ""}` },
    { title: "Account", dataIndex: "mt5_login", key: "mt5_login" },
    { title: "Campaign", dataIndex: "campaign_id", key: "campaign_id", render: (id: number | null) => id ? `#${id}` : "-" },
    { title: "Bonus", dataIndex: "bonus_id", key: "bonus_id", render: (id: number | null) => id ? `#${id}` : "-" },
    {
      title: "Before", dataIndex: "before_state", key: "before_state",
      render: (v: Record<string, unknown> | null) => v ? <code style={{ fontSize: 11 }}>{JSON.stringify(v).substring(0, 60)}</code> : "-",
    },
    {
      title: "After", dataIndex: "after_state", key: "after_state",
      render: (v: Record<string, unknown> | null) => v ? <code style={{ fontSize: 11 }}>{JSON.stringify(v).substring(0, 60)}</code> : "-",
    },
  ];

  return (
    <>
      <Typography.Title level={3}>Audit Log</Typography.Title>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search placeholder="MT5 Login" onSearch={(v) => { setLoginFilter(v); setPage(1); fetchData(); }} style={{ width: 200 }} allowClear />
        <Select placeholder="Event Type" allowClear style={{ width: 200 }} onChange={(v) => { setEventFilter(v || ""); setPage(1); }}
          options={[
            { label: "Assignment", value: "assignment" },
            { label: "Cancellation", value: "cancellation" },
            { label: "Conversion Step", value: "conversion_step" },
            { label: "Leverage Change", value: "leverage_change" },
            { label: "Expiry", value: "expiry" },
            { label: "Admin Override", value: "admin_override" },
          ]}
        />
      </Space>
      <Table columns={columns} dataSource={logs} rowKey="id" loading={loading} pagination={{ current: page, total, pageSize: 50, onChange: setPage }} size="small" />
    </>
  );
}
