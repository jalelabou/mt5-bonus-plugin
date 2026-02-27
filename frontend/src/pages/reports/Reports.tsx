import { useState } from "react";
import { Tabs, Table, Button, Space, Typography, message, Spin } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { getReportSummary, getReportConversions, getReportCancellations, getReportLeverage, exportReport } from "../../api/endpoints";

export default function Reports() {
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("summary");

  const load = async (key: string) => {
    setLoading(true);
    setActiveTab(key);
    try {
      let res;
      if (key === "summary") res = await getReportSummary();
      else if (key === "conversions") res = await getReportConversions();
      else if (key === "cancellations") res = await getReportCancellations();
      else res = await getReportLeverage();
      setData(res.data);
    } catch {
      message.error("Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    try {
      const res = await exportReport(activeTab, format);
      const blob = new Blob([res.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${activeTab}_report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      message.error("Export failed");
    }
  };

  const summaryColumns = [
    { title: "Campaign", dataIndex: "campaign_name", key: "campaign_name" },
    { title: "Type", dataIndex: "bonus_type", key: "bonus_type" },
    { title: "Issued", dataIndex: "total_issued", key: "total_issued" },
    { title: "Total Amount", dataIndex: "total_amount", key: "total_amount", render: (v: number) => `$${v?.toFixed(2) || 0}` },
    { title: "Active", dataIndex: "active_count", key: "active_count" },
    { title: "Cancelled", dataIndex: "cancelled_count", key: "cancelled_count" },
    { title: "Converted", dataIndex: "converted_count", key: "converted_count" },
  ];

  const conversionColumns = [
    { title: "Account", dataIndex: "mt5_login", key: "mt5_login" },
    { title: "Campaign", dataIndex: "campaign_name", key: "campaign_name" },
    { title: "Bonus", dataIndex: "bonus_amount", key: "bonus_amount", render: (v: number) => `$${v?.toFixed(2)}` },
    { title: "Lots Required", dataIndex: "lots_required", key: "lots_required" },
    { title: "Lots Traded", dataIndex: "lots_traded", key: "lots_traded", render: (v: number) => v?.toFixed(2) },
    { title: "% Complete", dataIndex: "percent_complete", key: "percent_complete", render: (v: number) => `${v?.toFixed(1)}%` },
    { title: "Converted", dataIndex: "amount_converted", key: "amount_converted", render: (v: number) => `$${v?.toFixed(2)}` },
  ];

  const cancellationColumns = [
    { title: "Account", dataIndex: "mt5_login", key: "mt5_login" },
    { title: "Campaign", dataIndex: "campaign_name", key: "campaign_name" },
    { title: "Amount", dataIndex: "bonus_amount", key: "bonus_amount", render: (v: number) => `$${v?.toFixed(2)}` },
    { title: "Reason", dataIndex: "reason", key: "reason" },
    { title: "Cancelled At", dataIndex: "cancelled_at", key: "cancelled_at" },
  ];

  const leverageColumns = [
    { title: "Account", dataIndex: "mt5_login", key: "mt5_login" },
    { title: "Campaign", dataIndex: "campaign_name", key: "campaign_name" },
    { title: "Original", dataIndex: "original_leverage", key: "original_leverage", render: (v: number) => `1:${v}` },
    { title: "Adjusted", dataIndex: "adjusted_leverage", key: "adjusted_leverage", render: (v: number) => `1:${v}` },
    { title: "Status", dataIndex: "status", key: "status" },
  ];

  const columnMap: Record<string, unknown[]> = {
    summary: summaryColumns,
    conversions: conversionColumns,
    cancellations: cancellationColumns,
    leverage: leverageColumns,
  };

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>Reports</Typography.Title>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={() => handleExport("csv")}>CSV</Button>
          <Button icon={<DownloadOutlined />} onClick={() => handleExport("xlsx")}>Excel</Button>
        </Space>
      </div>
      <Tabs
        onChange={load}
        items={[
          { key: "summary", label: "Bonus Summary" },
          { key: "conversions", label: "Conversion Progress" },
          { key: "cancellations", label: "Cancellations" },
          { key: "leverage", label: "Leverage Adjustments" },
        ]}
      />
      {loading ? (
        <Spin style={{ display: "block", margin: "40px auto" }} />
      ) : (
        <Table columns={columnMap[activeTab] as any} dataSource={data} rowKey={(_, i) => String(i)} size="small" />
      )}
    </>
  );
}
