import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Table, Tag, Space, Spin, Alert, message } from 'antd';
import { RobotOutlined, SendOutlined, UserOutlined, ReloadOutlined } from '@ant-design/icons';
import type { Candidate } from '@/types';
import * as hrApi from '@/api/hr';
import type { FilterRule } from '@/api/hr';

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待完善', color: 'default' },
  1: { text: '材料已提交', color: 'processing' },
  2: { text: '面试中', color: 'warning' },
  3: { text: '已完成', color: 'success' },
  4: { text: '已淘汰', color: 'error' },
};

type Message =
  | { type: 'user'; text: string }
  | { type: 'ai-rules'; text: string; rules: FilterRule }
  | { type: 'ai-results'; text: string; candidates: Candidate[]; total: number }
  | { type: 'ai-error'; text: string }
  | { type: 'ai-loading' };

export default function IntelligentFilter() {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      type: 'ai-rules' as const,
      text: '你好！我是智能筛选助手。请用自然语言描述你想筛选的候选人条件，例如：\n\n"驾龄3年以上、持有A2驾照且资格证在有效期内的候选人"',
      rules: { conditions: [], logic: 'AND', description: '' },
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    // 添加用户消息
    setMessages((prev) => [...prev, { type: 'user', text }]);
    setInput('');
    setLoading(true);

    // 添加加载状态
    setMessages((prev) => [...prev, { type: 'ai-loading' }]);

    try {
      const result = await hrApi.parseFilterRule(text);

      // 移除加载状态
      setMessages((prev) => prev.filter((m) => m.type !== 'ai-loading'));

      if (result.error) {
        setMessages((prev) => [
          ...prev,
          { type: 'ai-error', text: `解析失败：${result.error}` },
        ]);
      } else if (!result.conditions || result.conditions.length === 0) {
        setMessages((prev) => [
          ...prev,
          {
            type: 'ai-error',
            text: '未能从您的描述中解析出有效的筛选条件，请尝试更具体的描述。',
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            type: 'ai-rules',
            text: `已解析筛选规则：${result.description}`,
            rules: result as FilterRule,
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.type !== 'ai-loading'));
      setMessages((prev) => [
        ...prev,
        {
          type: 'ai-error',
          text: err instanceof Error ? err.message : '解析请求失败，请重试',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (rules: FilterRule) => {
    setLoading(true);
    try {
      const result = await hrApi.executeIntelligentFilter(rules);
      setMessages((prev) => [
        ...prev,
        {
          type: 'ai-results',
          text: `筛选完成，共找到 ${result.total} 位候选人`,
          candidates: result.items,
          total: result.total,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          type: 'ai-error',
          text: err instanceof Error ? err.message : '执行筛选失败',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        type: 'ai-rules' as const,
        text: '已清空对话。请用自然语言描述你想筛选的候选人条件。',
        rules: { conditions: [], logic: 'AND', description: '' },
      },
    ]);
    setInput('');
  };

  const resultColumns = [
    { title: '姓名', dataIndex: 'name', width: 100, render: (_v: string, record: Candidate) => (
      <Button type="link" size="small" style={{ padding: 0 }} onClick={() => navigate(`/hr/candidates/${record.id}`)}>
        {record.name || record.phone}
      </Button>
    )},
    { title: '手机号', dataIndex: 'phone', width: 130 },
    { title: '性别', dataIndex: 'gender', width: 60, render: (v: number) => v === 1 ? '男' : '女' },
    { title: '驾龄(年)', dataIndex: 'work_experience', width: 80 },
    { title: '总分', dataIndex: 'total_score', width: 80, render: (v: number) => v.toFixed(1) },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: number) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text}</Tag>,
    },
    {
      title: '操作', width: 120,
      render: (_: unknown, record: Candidate) => (
        <Button type="link" size="small" onClick={() => navigate(`/hr/candidates/${record.id}`)}>
          查看详情
        </Button>
      ),
    },
  ];

  const renderMessage = (msg: Message, idx: number) => {
    switch (msg.type) {
      case 'user':
        return (
          <div key={idx} style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <div style={{ maxWidth: '70%', background: '#1677ff', color: '#fff', padding: '12px 16px', borderRadius: 12, borderBottomRightRadius: 4 }}>
              {msg.text}
            </div>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#1677ff', display: 'flex', alignItems: 'center', justifyContent: 'center', marginLeft: 8, flexShrink: 0 }}>
              <UserOutlined style={{ color: '#fff' }} />
            </div>
          </div>
        );

      case 'ai-loading':
        return (
          <div key={idx} style={{ display: 'flex', marginBottom: 16 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8, flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#1677ff' }} />
            </div>
            <div style={{ background: '#f5f5f5', padding: '12px 16px', borderRadius: 12, borderBottomLeftRadius: 4 }}>
              <Spin size="small" /> 正在分析您的筛选需求...
            </div>
          </div>
        );

      case 'ai-error':
        return (
          <div key={idx} style={{ display: 'flex', marginBottom: 16 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#fff1f0', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8, flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#ff4d4f' }} />
            </div>
            <div style={{ maxWidth: '80%' }}>
              <Alert type="error" message={msg.text} style={{ margin: 0 }} />
            </div>
          </div>
        );

      case 'ai-rules': {
        const hasRules = msg.rules.conditions && msg.rules.conditions.length > 0;
        return (
          <div key={idx} style={{ display: 'flex', marginBottom: 16 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8, flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#1677ff' }} />
            </div>
            <div style={{ maxWidth: '85%' }}>
              <div style={{ background: '#f5f5f5', padding: '12px 16px', borderRadius: 12, borderBottomLeftRadius: 4 }}>
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                {hasRules && (
                  <div style={{ marginTop: 12, padding: 12, background: '#fff', borderRadius: 8, border: '1px solid #e8e8e8' }}>
                    <p style={{ margin: '0 0 8px 0', fontWeight: 600, color: '#333' }}>
                      逻辑关系：{msg.rules.logic === 'AND' ? '所有条件都满足（且）' : '满足任一条件（或）'}
                    </p>
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {msg.rules.conditions.map((cond, i) => (
                        <li key={i} style={{ marginBottom: 4 }}>
                          <code style={{ background: '#fafafa', padding: '1px 6px', borderRadius: 3, fontSize: 12 }}>
                            {cond.field}
                          </code>
                          <span style={{ margin: '0 4px', color: '#999' }}>
                            {cond.operator === 'eq' ? '=' : cond.operator === 'ne' ? '!=' : cond.operator === 'gt' ? '>' : cond.operator === 'gte' ? '>=' : cond.operator === 'lt' ? '<' : cond.operator === 'lte' ? '<=' : cond.operator === 'contains' ? '包含' : cond.operator}
                          </span>
                          <code style={{ background: '#fafafa', padding: '1px 6px', borderRadius: 3, fontSize: 12 }}>
                            {JSON.stringify(cond.value)}
                          </code>
                          <span style={{ marginLeft: 8, color: '#666' }}>{cond.description}</span>
                        </li>
                      ))}
                    </ul>
                    {msg.rules.limit_percent && (
                      <p style={{ margin: '8px 0 0 0', fontWeight: 600, color: '#1677ff' }}>
                        数量限制：前 {msg.rules.limit_percent}%
                      </p>
                    )}
                    {msg.rules.limit && (
                      <p style={{ margin: '8px 0 0 0', fontWeight: 600, color: '#1677ff' }}>
                        数量限制：前 {msg.rules.limit} 条
                      </p>
                    )}
                  </div>
                )}
              </div>
              {hasRules && (
                <div style={{ marginTop: 8 }}>
                  <Button type="primary" icon={<SendOutlined />} onClick={() => handleExecute(msg.rules)} loading={loading}>
                    执行筛选
                  </Button>
                  <span style={{ marginLeft: 12, fontSize: 12, color: '#999' }}>确认规则无误后点击执行</span>
                </div>
              )}
            </div>
          </div>
        );
      }

      case 'ai-results':
        return (
          <div key={idx} style={{ display: 'flex', marginBottom: 16 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#f6ffed', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8, flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#52c41a' }} />
            </div>
            <div style={{ maxWidth: '95%', flex: 1 }}>
              <div style={{ background: '#f5f5f5', padding: '12px 16px', borderRadius: 12, borderBottomLeftRadius: 4, marginBottom: 8 }}>
                <p style={{ margin: 0, color: '#52c41a', fontWeight: 500 }}>{msg.text}</p>
              </div>
              <Table
                size="small"
                rowKey="id"
                columns={resultColumns}
                dataSource={msg.candidates}
                pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
                style={{ background: '#fff' }}
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)', minHeight: 500 }}>
      {/* 顶部标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ fontSize: 20, color: '#1677ff' }} />
          <span style={{ fontSize: 16, fontWeight: 600 }}>AI 智能筛选助手</span>
        </div>
        <Button icon={<ReloadOutlined />} onClick={handleReset} disabled={loading}>
          清空对话
        </Button>
      </div>

      {/* 消息列表 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 0',
          border: '1px solid #f0f0f0',
          borderRadius: 8,
          paddingLeft: 16,
          paddingRight: 16,
          background: '#fafafa',
          marginBottom: 16,
        }}
      >
        {messages.map((msg, idx) => renderMessage(msg, idx))}
        <div ref={messagesEndRef} />
      </div>

      {/* 底部输入区 */}
      <div style={{ display: 'flex', gap: 8 }}>
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="描述你想筛选的候选人条件，例如：驾龄3年以上、持有A2驾照且资格证在有效期内的候选人"
          autoSize={{ minRows: 2, maxRows: 4 }}
          disabled={loading}
          style={{ flex: 1 }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={loading}
          disabled={!input.trim()}
          style={{ height: 'auto', minWidth: 80 }}
        >
          发送
        </Button>
      </div>
      <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
        按 Enter 发送，Shift + Enter 换行
      </div>
    </div>
  );
}
