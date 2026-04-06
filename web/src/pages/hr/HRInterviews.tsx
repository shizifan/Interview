import { useEffect, useState } from 'react';
import { Table, Tag, Button, Modal, Descriptions, List } from 'antd';
import type { Interview, InterviewDetail } from '@/types';
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
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<InterviewDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const load = (p: number) => {
    setLoading(true);
    hrApi.getInterviews(p, 20)
      .then((res) => { setInterviews(res.items); setTotal(res.total); setPage(p); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, []);

  const showDetail = async (interviewId: number) => {
    setDetailOpen(true);
    setDetailLoading(true);
    try {
      const data = await hrApi.getInterviewDetail(interviewId);
      setDetail(data);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

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
    {
      title: '操作', width: 80,
      render: (_: unknown, record: Interview) => (
        <Button type="link" size="small" onClick={() => showDetail(record.id)}>
          详情
        </Button>
      ),
    },
  ];

  return (
    <>
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
      <Modal
        title="面试详情"
        open={detailOpen}
        onCancel={() => { setDetailOpen(false); setDetail(null); }}
        footer={null}
        width={700}
        loading={detailLoading}
      >
        {detail && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="候选人">{detail.candidate_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="岗位">{detail.job_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[detail.interview.status]?.color}>
                  {statusMap[detail.interview.status]?.text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="总分">{detail.interview.total_score?.toFixed(1) ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="开始时间" span={2}>
                {new Date(detail.interview.created_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
            </Descriptions>

            {detail.answers.length > 0 && (
              <>
                <h4 style={{ marginBottom: 8 }}>回答记录</h4>
                <List
                  size="small"
                  bordered
                  dataSource={detail.answers}
                  renderItem={(ans) => (
                    <List.Item>
                      <div style={{ width: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span style={{ fontWeight: 500 }}>第 {ans.question_order} 题</span>
                          <Tag color={ans.score >= 7 ? 'green' : ans.score >= 4 ? 'orange' : 'red'}>
                            {ans.score} 分
                          </Tag>
                        </div>
                        <div style={{ color: '#666', fontSize: 13 }}>
                          {ans.answer_text || '(未回答)'}
                        </div>
                        {ans.follow_up_count > 0 && (
                          <div style={{ color: '#999', fontSize: 12, marginTop: 2 }}>
                            追问 {ans.follow_up_count} 次
                          </div>
                        )}
                      </div>
                    </List.Item>
                  )}
                />
              </>
            )}

            {detail.interview.report_content && (
              <div style={{ marginTop: 16 }}>
                <h4 style={{ marginBottom: 8 }}>AI评估报告</h4>
                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 6, whiteSpace: 'pre-wrap', fontSize: 13 }}>
                  {detail.interview.report_content}
                </div>
              </div>
            )}
          </>
        )}
      </Modal>
    </>
  );
}
