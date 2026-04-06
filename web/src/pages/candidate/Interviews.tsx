import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';
import { useInterviewStore } from '@/stores/interviewStore';
import type { Interview, Job } from '@/types';
import * as candidateApi from '@/api/candidate';
import * as hrApi from '@/api/hr';

const statusMap: Record<number, { label: string; color: string }> = {
  0: { label: '待开始', color: 'bg-gray-100 text-gray-600' },
  1: { label: '进行中', color: 'bg-blue-100 text-blue-600' },
  2: { label: '已完成', color: 'bg-green-100 text-green-600' },
  3: { label: '已中断', color: 'bg-red-100 text-red-600' },
  4: { label: '已过期', color: 'bg-gray-100 text-gray-400' },
};

export default function Interviews() {
  const { candidate } = useCandidateStore();
  const { startInterview } = useInterviewStore();
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (!candidate) {
      navigate('/');
      return;
    }
    setLoading(true);
    Promise.all([
      candidateApi.listInterviews(candidate.id),
      hrApi.getJobs(1, 50),
    ])
      .then(([ivs, jobRes]) => {
        setInterviews(ivs);
        setJobs(jobRes.items.filter((j) => j.status === 1));
      })
      .finally(() => setLoading(false));
  }, [candidate, navigate]);

  const handleStart = async (jobId: number) => {
    if (!candidate) return;
    setStarting(true);
    try {
      await startInterview(candidate.id, jobId);
      const { interviewId } = useInterviewStore.getState();
      if (interviewId) {
        navigate(`/interview/${interviewId}`);
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : '启动面试失败');
    } finally {
      setStarting(false);
    }
  };

  const handleResume = (interviewId: number) => {
    navigate(`/interview/${interviewId}`);
  };

  if (!candidate) return null;

  return (
    <div className="space-y-4 pb-20">
      <h2 className="text-xl font-bold text-gray-800">我的面试</h2>

      {/* 可面试岗位 */}
      {jobs.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">开始新面试</h3>
          <div className="space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="bg-white rounded-xl p-4 shadow-sm flex justify-between items-center">
                <div>
                  <div className="font-medium text-gray-800">{job.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{job.description}</div>
                </div>
                <button
                  onClick={() => handleStart(job.id)}
                  disabled={starting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  开始面试
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 面试记录 */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 mb-2">面试记录</h3>
        {loading ? (
          <div className="text-center text-gray-400 py-8">加载中...</div>
        ) : interviews.length === 0 ? (
          <div className="text-center text-gray-400 py-8 bg-white rounded-xl shadow-sm">暂无面试记录</div>
        ) : (
          <div className="space-y-2">
            {interviews.map((iv) => {
              const st = statusMap[iv.status] || statusMap[0];
              return (
                <div
                  key={iv.id}
                  className="bg-white rounded-xl p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => {
                    if (iv.status === 2) navigate(`/interview/${iv.id}/result`);
                    else if (iv.status === 1) handleResume(iv.id);
                  }}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-gray-800">面试 #{iv.id}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(iv.created_at).toLocaleString('zh-CN')}
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${st.color}`}>
                      {st.label}
                    </span>
                  </div>
                  {iv.status === 2 && (
                    <div className="mt-2 text-sm text-blue-600">得分: {iv.total_score}分 &gt;</div>
                  )}
                  {iv.status === 1 && (
                    <div className="mt-2 text-sm text-orange-600">点击继续面试 &gt;</div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
