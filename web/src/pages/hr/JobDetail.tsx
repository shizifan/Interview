import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Table, Button, Modal, Form, Input, InputNumber, Space, message, Popconfirm, Switch } from 'antd';
import { PlusOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import type { Job, Question, QuestionCreate } from '@/types';
import * as hrApi from '@/api/hr';

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingQ, setEditingQ] = useState<Question | null>(null);
  const [form] = Form.useForm<QuestionCreate>();

  const jid = Number(jobId);

  const loadData = () => {
    setLoading(true);
    Promise.all([hrApi.getJob(jid), hrApi.getQuestions(jid)])
      .then(([j, qs]) => { setJob(j); setQuestions(qs); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, [jid]);

  const handleSubmit = async () => {
    const values = await form.validateFields();
    const payload = { ...values, job_id: jid };
    if (editingQ) {
      await hrApi.updateQuestion(editingQ.id, payload);
      message.success('更新成功');
    } else {
      await hrApi.createQuestion(payload);
      message.success('创建成功');
    }
    setModalOpen(false);
    form.resetFields();
    setEditingQ(null);
    loadData();
  };

  const handleDelete = async (id: number) => {
    await hrApi.deleteQuestion(id);
    message.success('删除成功');
    loadData();
  };

  const columns = [
    { title: '序号', dataIndex: 'sort_order', width: 60 },
    { title: '题目内容', dataIndex: 'content' },
    {
      title: '启用', dataIndex: 'is_active', width: 80,
      render: (v: boolean) => <Switch checked={v} disabled size="small" />,
    },
    {
      title: '操作', width: 150,
      render: (_: unknown, record: Question) => (
        <Space>
          <Button type="link" size="small" onClick={() => {
            setEditingQ(record);
            form.setFieldsValue({
              content: record.content,
              sort_order: record.sort_order,
              score_points: record.score_points,
              follow_up_scripts: record.follow_up_scripts,
            });
            setModalOpen(true);
          }}>
            编辑
          </Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/hr/jobs')}>返回</Button>
        <span style={{ fontSize: 16, fontWeight: 500 }}>
          {job?.name || '加载中...'} - 面试题目
        </span>
      </Space>

      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => {
          setEditingQ(null); form.resetFields(); setModalOpen(true);
        }}>
          添加题目
        </Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={questions} loading={loading} pagination={false} />

      <Modal
        title={editingQ ? '编辑题目' : '添加题目'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => { setModalOpen(false); setEditingQ(null); }}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="content" label="题目内容" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="请输入面试题目" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序" initialValue={1}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="score_points" label="得分要点（JSON数组）" help="如: [&quot;安全意识&quot;, &quot;操作规范&quot;]">
            <Input.TextArea rows={2} placeholder='["要点1", "要点2"]' />
          </Form.Item>
          <Form.Item name="follow_up_scripts" label="追问话术（JSON数组）">
            <Input.TextArea rows={2} placeholder='["追问1", "追问2"]' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
