import { useEffect, useState } from 'react';
import { Table, Select, Tag } from 'antd';
import type { ScorePoolEntry, Job } from '@/types';
import * as hrApi from '@/api/hr';

export default function ScorePool() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [entries, setEntries] = useState<ScorePoolEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    hrApi.getJobs(1, 100).then((res) => {
      setJobs(res.items);
      if (res.items.length > 0) setSelectedJobId(res.items[0].id);
    });
  }, []);

  useEffect(() => {
    if (selectedJobId === null) return;
    setLoading(true);
    hrApi.getScorePool(selectedJobId).then((res) => setEntries(res.items)).finally(() => setLoading(false));
  }, [selectedJobId]);

  const columns = [
    { title: '排名', dataIndex: 'rank', width: 60, render: (v: number | null) => v ?? '-' },
    { title: '候选人', dataIndex: 'candidate_name', render: (v: string) => v || '-' },
    { title: '手机号', dataIndex: 'candidate_phone' },
    { title: '材料分', dataIndex: 'doc_score', width: 80, render: (v: number) => v?.toFixed(1) },
    { title: '面试分', dataIndex: 'interview_score', width: 80, render: (v: number) => v?.toFixed(1) },
    { title: '总分', dataIndex: 'total_score', width: 80, render: (v: number) => v?.toFixed(1) },
    {
      title: '邀约', dataIndex: 'is_invited', width: 80,
      render: (v: boolean) => v ? <Tag color="green">已邀约</Tag> : <Tag>未邀约</Tag>,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <span style={{ marginRight: 8 }}>选择岗位：</span>
        <Select
          value={selectedJobId}
          onChange={setSelectedJobId}
          style={{ width: 200 }}
          options={jobs.map((j) => ({ value: j.id, label: j.name }))}
          placeholder="选择岗位"
        />
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={entries}
        loading={loading}
        pagination={false}
      />
    </div>
  );
}
