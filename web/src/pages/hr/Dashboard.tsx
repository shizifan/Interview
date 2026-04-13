import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic } from 'antd';
import {
  TeamOutlined,
  SolutionOutlined,
  CheckCircleOutlined,
  FileSearchOutlined,
} from '@ant-design/icons';
import type { DashboardStats } from '@/types';
import * as hrApi from '@/api/hr';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hrApi.getDashboard().then(setStats).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="今日面试"
              value={stats?.today_interviews ?? 0}
              prefix={<SolutionOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="已完成面试"
              value={stats?.completed_interviews ?? 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="通过率"
              value={stats?.pass_rate ?? 0}
              suffix="%"
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="待审核材料"
              value={stats?.pending_documents ?? 0}
              prefix={<FileSearchOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="候选人总数" style={{ marginTop: 16 }} loading={loading}>
        <Statistic value={stats?.total_candidates ?? 0} suffix="人" />
      </Card>
    </div>
  );
}
