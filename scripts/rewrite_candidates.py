p = 'web/src/pages/hr/Candidates.tsx'
new_content = '''import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Tag, Input, Button, Modal, Select, message, Space } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import type { Candidate, Job } from '@/types';
import * as hrApi from '@/api/hr';

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待完善', color: 'default' },
  1: { text: '材料已提交', color: 'processing' },
  2: { text: '面试中', color: 'warning' },
  3: { text: '已完成', color: 'success' },
  4: { text: '已淘汰', color: 'error' },
};

export default function Candidates() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [inviting, setInviting] = useState(false);

  const load = (p: number) => {
    setLoading(true);
    hrApi.getCandidates(p, 20)
      .then((res) => { setCandidates(res.items); setTotal(res.total); setPage(p); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, []);

  const openInvite = (candidate: Candidate) => {
    setSelectedCandidate(candidate);
    setSelectedJobId(null);
    hrApi.getJobs(1, 100).then((res) => setJobs(res.items));
    setInviteModalOpen(true);
  };

  const handleInvite = async () => {
    if (!selectedCandidate || !selectedJobId) return;
    setInviting(true);
    try {
      await hrApi.inviteCandidate(selectedCandidate.id, selectedJobId);
      message.success('邀约面试成功');
      setInviteModalOpen(false);
      load(page);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '邀约失败');
    } finally {
      setInviting(false);
    }
  };

  const goToFilter = () => {
    navigate('/hr/intelligent-filter');
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '姓名', dataIndex: 'name', render: (_v: string, record: Candidate) => (
      <Button type="link" size="small" style={{ padding: 0 }} onClick={() => navigate(`/hr/candidates/${record.id}`)}>{record.name || record.phone}</Button>
    ) },
    { title: '手机号', dataIndex: 'phone' },
    { title: '性别', dataIndex: 'gender', width: 60, render: (v: number) => v === 1 ? '男' : '女' },
    { title: '驾龄(年)', dataIndex: 'work_experience', width: 80 },
    { title: '总分', dataIndex: 'total_score', width: 80, render: (v: number) => v.toFixed(1) },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: number) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag>,
    },
    { title: '注册时间', dataIndex: 'created_at', width: 180, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    {
      title: '操作', width: 160,
      render: (_: unknown, record: Candidate) => (
        <Space>
          <Button type="link" size="small" onClick={() => navigate(`/hr/candidates/${record.id}`)}>
            查看
          </Button>
          <Button type="link" size="small" onClick={() => openInvite(record)}>
            邀约面试
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <Input.Search
          placeholder="搜索候选人姓名或手机号"
          style={{ width: 300 }}
          allowClear
          onSearch={() => load(1)}
        />
        <Button icon={<RobotOutlined />} type="default" onClick={goToFilter}>
          智能筛选
        </Button>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={candidates}
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: load,
          showTotal: (t) => `共 ${t} 条`,
        }}
      />
      <Modal
        title={`邀约面试 - ${selectedCandidate?.name || selectedCandidate?.phone || ''}`}
        open={inviteModalOpen}
        onOk={handleInvite}
        onCancel={() => setInviteModalOpen(false)}
        confirmLoading={inviting}
        okButtonProps={{ disabled: !selectedJobId }}
      >
        <div style={{ marginBottom: 8 }}>请选择面试岗位：</div>
        <Select
          style={{ width: '100%' }}
          placeholder="选择岗位"
          value={selectedJobId}
          onChange={setSelectedJobId}
          options={jobs.filter((j) => j.status === 1).map((j) => ({ label: j.name, value: j.id }))}
        />
      </Modal>
    </div>
  );
}
'''
with open(p, 'w', encoding='utf-8') as f:
    f.write(new_content)
print('OK')
