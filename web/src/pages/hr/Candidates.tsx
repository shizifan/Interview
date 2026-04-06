import { useEffect, useState } from 'react';
import { Table, Tag, Input } from 'antd';
import type { Candidate } from '@/types';
import * as hrApi from '@/api/hr';

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待完善', color: 'default' },
  1: { text: '材料已提交', color: 'processing' },
  2: { text: '面试中', color: 'warning' },
  3: { text: '已完成', color: 'success' },
  4: { text: '已淘汰', color: 'error' },
};

export default function Candidates() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const load = (p: number) => {
    setLoading(true);
    hrApi.getCandidates(p, 20)
      .then((res) => { setCandidates(res.items); setTotal(res.total); setPage(p); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, []);

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '姓名', dataIndex: 'name', render: (v: string) => v || '-' },
    { title: '手机号', dataIndex: 'phone' },
    { title: '性别', dataIndex: 'gender', width: 60, render: (v: number) => v === 1 ? '男' : '女' },
    { title: '驾龄(年)', dataIndex: 'work_experience', width: 80 },
    { title: '总分', dataIndex: 'total_score', width: 80, render: (v: number) => v.toFixed(1) },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: number) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag>,
    },
    { title: '注册时间', dataIndex: 'created_at', width: 180, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索候选人姓名或手机号"
          style={{ width: 300 }}
          allowClear
          onSearch={() => load(1)}
        />
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
    </div>
  );
}
