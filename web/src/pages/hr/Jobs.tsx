import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, Select, Space, Tag, message, Popconfirm } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { Job, JobCreate } from '@/types';
import * as hrApi from '@/api/hr';

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '草稿', color: 'default' },
  1: { text: '招聘中', color: 'green' },
  2: { text: '已关闭', color: 'red' },
};

const licenseOptions = ['A1', 'A2', 'A3', 'B1', 'B2', 'C1', 'C2', 'C3', 'D', 'E'].map((v) => ({ label: v, value: v }));

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [form] = Form.useForm<JobCreate>();
  const navigate = useNavigate();

  const loadJobs = () => {
    setLoading(true);
    hrApi.getJobs(1, 100).then((res) => setJobs(res.items)).finally(() => setLoading(false));
  };

  useEffect(() => { loadJobs(); }, []);

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingJob) {
      await hrApi.updateJob(editingJob.id, values);
      message.success('更新成功');
    } else {
      await hrApi.createJob(values);
      message.success('创建成功');
    }
    setModalOpen(false);
    form.resetFields();
    setEditingJob(null);
    loadJobs();
  };

  const handleDelete = async (id: number) => {
    await hrApi.deleteJob(id);
    message.success('删除成功');
    loadJobs();
  };

  const openEdit = (job: Job) => {
    setEditingJob(job);
    let licenseTypes: string[] = [];
    if (job.required_license_type) {
      try {
        licenseTypes = JSON.parse(job.required_license_type);
      } catch {
        licenseTypes = [];
      }
    }
    form.setFieldsValue({
      name: job.name,
      description: job.description,
      requirements: job.requirements,
      quota: job.quota,
      start_coefficient: job.start_coefficient,
      min_interview_count: job.min_interview_count,
      required_license_type: licenseTypes,
    });
    setModalOpen(true);
  };

  const parseLicenseType = (v: string | null | undefined): string[] => {
    if (!v) return [];
    try { return JSON.parse(v); } catch { return []; }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '岗位名称', dataIndex: 'name' },
    { title: '招聘人数', dataIndex: 'quota', width: 100 },
    {
      title: '准驾类型', dataIndex: 'required_license_type', width: 160,
      render: (v: string | null) => {
        const types = parseLicenseType(v);
        return types.length > 0
          ? types.map((t) => <Tag key={t} color="blue">{t}</Tag>)
          : <span style={{ color: '#999' }}>不限</span>;
      },
    },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: number) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', width: 180, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    {
      title: '操作', width: 200,
      render: (_: unknown, record: Job) => (
        <Space>
          <Button type="link" size="small" onClick={() => navigate(`/hr/jobs/${record.id}`)}>题目</Button>
          <Button type="link" size="small" onClick={() => openEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { setEditingJob(null); form.resetFields(); setModalOpen(true); }}
        >
          新建岗位
        </Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={jobs} loading={loading} pagination={false} />

      <Modal
        title={editingJob ? '编辑岗位' : '新建岗位'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => { setModalOpen(false); setEditingJob(null); }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="岗位名称" rules={[{ required: true }]}>
            <Input placeholder="如: 卡车司机" />
          </Form.Item>
          <Form.Item name="description" label="岗位描述" rules={[{ required: true }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="requirements" label="任职要求">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="required_license_type" label="要求准驾类型">
            <Select mode="multiple" placeholder="选择准驾类型（不选表示不限）" options={licenseOptions} allowClear />
          </Form.Item>
          <Form.Item name="quota" label="招聘人数" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="start_coefficient" label="启动系数" initialValue={1.2}>
            <InputNumber min={0.1} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="min_interview_count" label="最少面试人数" initialValue={5}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
