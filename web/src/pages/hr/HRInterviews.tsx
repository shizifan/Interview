import { useEffect, useState } from 'react';
import { Table, Tag } from 'antd';
import type { Interview } from '@/types';
import * as hrApi from '@/api/hr';

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待开始', color: 'default' },
  1: { text: '进行中', color: 'processing' },
  2: { text: '已完成', color: 'success' },
  3: { text: '已中断', color: 'error' },
  4: { text: '已过期', color: 'default' },
};

export default function HRInterviews() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const load = (p: number) => {
    setLoading(true);
    hrApi.getInterviews(p, 20)
      .then((res) => { setInterviews(res.items); setTotal(res.total); setPage(p); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, []);

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '候选人ID', dataIndex: 'candidate_id', width: 100 },
    { title: '岗位ID', dataIndex: 'job_id', width: 80 },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: number) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag>,
    },
    { title: '当前节点', dataIndex: 'current_node', width: 120 },
    { title: '总分', dataIndex: 'total_score', width: 80, render: (v: number) => v?.toFixed(1) ?? '-' },
    { title: '开始时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    { title: '更新时间', dataIndex: 'updated_at', render: (v: string) => new Date(v).toLocaleString('zh-CN') },
  ];

  return (
    <Table
      rowKey="id"
      columns={columns}
      dataSource={interviews}
      loading={loading}
      pagination={{
        current: page,
        total,
        pageSize: 20,
        onChange: load,
        showTotal: (t) => `共 ${t} 条`,
      }}
    />
  );
}
