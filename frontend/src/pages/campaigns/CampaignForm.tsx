import { useEffect, useState } from "react";
import { Form, Input, InputNumber, Select, Switch, Button, Card, Typography, DatePicker, message, Space } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { createCampaign, getCampaign, updateCampaign } from "../../api/endpoints";
import dayjs from "dayjs";

export default function CampaignForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [bonusType, setBonusType] = useState("B");
  const navigate = useNavigate();

  useEffect(() => {
    if (isEdit) {
      getCampaign(Number(id)).then((res) => {
        const data = { ...res.data } as Record<string, unknown>;
        if (data.start_date) data.start_date = dayjs(data.start_date as string);
        if (data.end_date) data.end_date = dayjs(data.end_date as string);
        form.setFieldsValue(data);
        setBonusType((data.bonus_type as string) || "B");
      });
    }
  }, [id]);

  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      if (values.start_date) values.start_date = (values.start_date as dayjs.Dayjs).toISOString();
      if (values.end_date) values.end_date = (values.end_date as dayjs.Dayjs).toISOString();
      if (isEdit) {
        await updateCampaign(Number(id), values);
        message.success("Campaign updated");
      } else {
        await createCampaign(values);
        message.success("Campaign created");
      }
      navigate("/campaigns");
    } catch (err: any) {
      message.error(err.response?.data?.detail || "Failed to save campaign");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Typography.Title level={3}>{isEdit ? "Edit Campaign" : "New Campaign"}</Typography.Title>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ bonus_type: "B", bonus_percentage: 100, max_concurrent_bonuses: 1, one_bonus_per_account: false, trigger_types: [] }}>
          <Form.Item name="name" label="Campaign Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>

          <Space size="large" wrap>
            <Form.Item name="bonus_type" label="Bonus Type" rules={[{ required: true }]}>
              <Select style={{ width: 200 }} onChange={(v) => setBonusType(v)} options={[
                { label: "Type A - Dynamic Leverage", value: "A" },
                { label: "Type B - Fixed Leverage", value: "B" },
                { label: "Type C - Convertible", value: "C" },
              ]} />
            </Form.Item>
            <Form.Item name="bonus_percentage" label="Bonus %" rules={[{ required: true }]}>
              <InputNumber min={1} max={1000} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="max_bonus_amount" label="Max Bonus ($)">
              <InputNumber min={0} style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space size="large" wrap>
            <Form.Item name="min_deposit" label="Min Deposit ($)">
              <InputNumber min={0} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="max_deposit" label="Max Deposit ($)">
              <InputNumber min={0} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="expiry_days" label="Expiry (days)">
              <InputNumber min={1} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          {bonusType === "C" && (
            <Space size="large" wrap>
              <Form.Item name="lot_requirement" label="Lot Requirement">
                <InputNumber min={0.01} step={0.1} style={{ width: 150 }} />
              </Form.Item>
              <Form.Item name="lot_tracking_scope" label="Lot Tracking Scope">
                <Select style={{ width: 200 }} options={[
                  { label: "All lots", value: "all" },
                  { label: "Post-bonus only", value: "post_bonus" },
                  { label: "Symbol filtered", value: "symbol_filtered" },
                  { label: "Per-trade threshold", value: "per_trade_threshold" },
                ]} />
              </Form.Item>
              <Form.Item name="per_trade_lot_minimum" label="Per-Trade Min Lots">
                <InputNumber min={0.01} step={0.01} style={{ width: 150 }} />
              </Form.Item>
            </Space>
          )}

          <Form.Item name="trigger_types" label="Trigger Types">
            <Select mode="multiple" style={{ width: "100%" }} options={[
              { label: "Auto on Deposit", value: "auto_deposit" },
              { label: "Promo Code", value: "promo_code" },
              { label: "Registration", value: "registration" },
              { label: "Agent Code", value: "agent_code" },
            ]} />
          </Form.Item>

          <Space size="large" wrap>
            <Form.Item name="promo_code" label="Promo Code">
              <Input style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="start_date" label="Start Date">
              <DatePicker showTime />
            </Form.Item>
            <Form.Item name="end_date" label="End Date">
              <DatePicker showTime />
            </Form.Item>
          </Space>

          <Space size="large" wrap>
            <Form.Item name="one_bonus_per_account" label="One Per Account" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="max_concurrent_bonuses" label="Max Concurrent Bonuses">
              <InputNumber min={1} max={10} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          <Form.Item name="notes" label="Notes / T&C">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {isEdit ? "Update" : "Create"} Campaign
            </Button>
            <Button onClick={() => navigate("/campaigns")}>Cancel</Button>
          </Space>
        </Form>
      </Card>
    </>
  );
}
