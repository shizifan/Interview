import { useEffect, useState } from 'react';
import { Form, InputNumber, Button, Card, message, Spin } from 'antd';
import type { SystemSettings } from '@/types';
import * as hrApi from '@/api/hr';

export default function Settings() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    hrApi.getSettings().then((s) => {
      setSettings(s);
      const values: Record<string, number> = {};
      for (const [key, item] of Object.entries(s)) {
        values[key] = Number(item.value);
      }
      form.setFieldsValue(values);
    }).finally(() => setLoading(false));
  }, [form]);

  const handleSave = async () => {
    const values = await form.validateFields();
    const data: Record<string, string> = {};
    for (const [k, v] of Object.entries(values)) {
      data[k] = String(v);
    }
    setSaving(true);
    try {
      const updated = await hrApi.updateSettings(data);
      setSettings(updated);
      message.success('保存成功');
    } catch (e) {
      message.error(e instanceof Error ? e.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spin />;

  return (
    <Card title="系统设置">
      <Form form={form} layout="vertical" style={{ maxWidth: 500 }}>
        {settings && Object.entries(settings).map(([key, item]) => (
          <Form.Item key={key} name={key} label={item.description}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        ))}
        <Form.Item>
          <Button type="primary" onClick={handleSave} loading={saving}>
            保存设置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}
