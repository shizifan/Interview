import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Descriptions, Table, Tag, Space, Image, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import type { Candidate, Document, Interview } from '@/types';
import * as hrApi from '@/api/hr';

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待完善', color: 'default' },
  1: { text: '材料已提交', color: 'processing' },
  2: { text: '面试中', color: 'warning' },
  3: { text: '已完成', color: 'success' },
  4: { text: '已淘汰', color: 'error' },
};

const docTypeMap: Record<number, string> = {
  1: '身份证',
  2: '驾驶证',
  3: '从业资格证',
  4: '体检报告',
};

const interviewStatusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待开始', color: 'default' },
  1: { text: '进行中', color: 'processing' },
  2: { text: '已完成', color: 'success' },
  3: { text: '已中断', color: 'error' },
  4: { text: '已过期', color: 'default' },
};

export default function CandidateDetail() {
  const { candidateId } = useParams<{ candidateId: string }>();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);

  const cid = Number(candidateId);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      hrApi.getCandidate(cid),
      hrApi.getCandidateDocuments(cid),
      hrApi.getCandidateInterviews(cid),
    ])
      .then(([c, docs, ivs]) => {
        setCandidate(c);
        setDocuments(docs);
        setInterviews(ivs);
      })
      .catch(() => message.error('加载候选人信息失败'))
      .finally(() => setLoading(false));
  }, [cid]);

  const docColumns = [
    { title: '类型', dataIndex: 'type', width: 120, render: (v: number) => docTypeMap[v] || `类型${v}` },
    {
      title: '文件', dataIndex: 'file_path', width: 120,
      render: (v: string) => v ? <Image src={`/api/v1/files/${v}`} width={80} fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN8/+F/PQAJpAN12gMkzAAAAABJRU5ErkJggg==" /> : '-',
    },
    {
      title: 'OCR 结果', dataIndex: 'ocr_result',
      render: (v: Record<string, string> | null) => {
        if (!v) return <span style={{ color: '#999' }}>未识别</span>;
        return (
          <div>
            {Object.entries(v).map(([key, val]) => (
              <div key={key}><strong>{key}:</strong> {val}</div>
            ))}
          </div>
        );
      },
    },
    { title: '评分', dataIndex: 'score', width: 80, render: (v: number) => v > 0 ? v.toFixed(1) : '-' },
    { title: '上传时间', dataIndex: 'created_at', width: 180, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
  ];

  const interviewColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: number) => <Tag color={interviewStatusMap[v]?.color}>{interviewStatusMap[v]?.text}</Tag>,
    },
    { title: '得分', dataIndex: 'total_score', width: 80, render: (v: number) => v > 0 ? v.toFixed(1) : '-' },
    { title: '开始时间', dataIndex: 'created_at', width: 180, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    {
      title: '操作', width: 100,
      render: (_: unknown, record: Interview) => (
        record.status === 2 ? (
          <Button type="link" size="small" onClick={() => navigate(`/hr/interviews/${record.id}`)}>
            查看详情
          </Button>
        ) : null
      ),
    },
  ];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>加载中...</div>;
  }

  if (!candidate) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>候选人不存在</div>;
  }

  const st = statusMap[candidate.status] || statusMap[0];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/hr/candidates')}>返回</Button>
        <span style={{ fontSize: 16, fontWeight: 500 }}>
          候选人详情 - {candidate.name || candidate.phone}
        </span>
      </Space>

      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={3}>
          <Descriptions.Item label="姓名">{candidate.name || '-'}</Descriptions.Item>
          <Descriptions.Item label="手机号">{candidate.phone}</Descriptions.Item>
          <Descriptions.Item label="性别">{candidate.gender === 1 ? '男' : '女'}</Descriptions.Item>
          <Descriptions.Item label="年龄">{candidate.age ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="学历">{candidate.education || '-'}</Descriptions.Item>
          <Descriptions.Item label="驾龄(年)">{candidate.work_experience}</Descriptions.Item>
          <Descriptions.Item label="身份证号">{candidate.id_card || '-'}</Descriptions.Item>
          <Descriptions.Item label="地址">{candidate.address || '-'}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={st.color}>{st.text}</Tag></Descriptions.Item>
          <Descriptions.Item label="综合评分">{candidate.total_score.toFixed(1)}</Descriptions.Item>
          <Descriptions.Item label="注册时间">{new Date(candidate.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title={`资质材料 (${documents.length})`} style={{ marginBottom: 16 }}>
        {documents.length > 0 ? (
          <Table rowKey="id" columns={docColumns} dataSource={documents} pagination={false} size="small" />
        ) : (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无材料</div>
        )}
      </Card>

      <Card title={`面试记录 (${interviews.length})`}>
        {interviews.length > 0 ? (
          <Table rowKey="id" columns={interviewColumns} dataSource={interviews} pagination={false} size="small" />
        ) : (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无面试记录</div>
        )}
      </Card>
    </div>
  );
}
