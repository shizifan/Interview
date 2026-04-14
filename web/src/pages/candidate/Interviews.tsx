import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';
import { useInterviewStore } from '@/stores/interviewStore';
import type { Interview, Job } from '@/types';
import * as candidateApi from '@/api/candidate';
import { groupInterviewsByJob } from '@/utils/groupInterviews';

const statusMap: Record<number, { label: string; color: string }> = {
  0: { label: '待开始', color: 'bg-gray-100 text-gray-600' },
  1: { label: '进行中', color: 'bg-blue-100 text-blue-600' },
  2: { label: '已完成', color: 'bg-green-100 text-green-600' },
  3: { label: '已中断', color: 'bg-red-100 text-red-600' },
  4: { label: '已过期', color: 'bg-gray-100 text-gray-400' },
};

function InterviewRow({ iv, onClick }: { iv: Interview; onClick: () => void }) {
  const st = statusMap[iv.status] || statusMap[0];
  const clickable = iv.status === 1 || iv.status === 2;
  return (
    <div
      className={`flex items-center justify-between py-2 px-3 rounded-lg ${clickable ? 'cursor-pointer hover:bg-gray-50' : ''}`}
      onClick={clickable ? onClick : undefined}
    >
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>#{iv.id}</span>
        <span>{new Date(iv.created_at).toLocaleString('zh-CN')}</span>
        {iv.status === 2 && iv.total_score > 0 && (
          <span className="text-green-600">{iv.total_score}分</span>
        )}
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full ${st.color}`}>{st.label}</span>
    </div>
  );
}

export default function Interviews() {
  const { candidate } = useCandidateStore();
  const { startInterview } = useInterviewStore();
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null);

  const groups = useMemo(
    () => groupInterviewsByJob(interviews, jobs),
    [interviews, jobs],
  );

  useEffect(() => {
    if (!candidate) return;
    setLoading(true);
    Promise.all([
      candidateApi.listInterviews(candidate.id),
      candidateApi.getJobs(),
    ])
      .then(([ivs, jobList]) => {
        setInterviews(ivs);
        setJobs(jobList);
      })
      .finally(() => setLoading(false));
  }, [candidate]);

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

  const navigateInterview = (iv: Interview) => {
    if (iv.status === 2) navigate(`/interview/${iv.id}/result`);
    else if (iv.status === 1) navigate(`/interview/${iv.id}`);
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
        ) : groups.length === 0 ? (
          <div className="text-center text-gray-400 py-8 bg-white rounded-xl shadow-sm">暂无面试记录</div>
        ) : (
          <div className="space-y-2">
            {groups.map((group) => {
              const rep = group.representative;
              const st = statusMap[rep.status] || statusMap[0];
              const clickable = rep.status === 1 || rep.status === 2;
              const expanded = expandedJobId === group.job_id;
              const hasHistory = group.history.length > 1;

              return (
                <div key={group.job_id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                  {/* 主卡片 */}
                  <div
                    className={`p-4 ${clickable ? 'cursor-pointer hover:bg-gray-50' : ''} transition-colors`}
                    onClick={() => clickable && navigateInterview(rep)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-gray-800">{group.job_name}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(rep.created_at).toLocaleString('zh-CN')}
                          {hasHistory && (
                            <span className="ml-2 text-gray-400">共{group.history.length}次</span>
                          )}
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${st.color}`}>
                        {st.label}
                      </span>
                    </div>
                    {rep.status === 2 && (
                      <div className="mt-2 text-sm text-green-600">
                        得分: {rep.total_score}分 &gt;
                      </div>
                    )}
                    {rep.status === 1 && (
                      <div className="mt-2 text-sm text-orange-600">点击继续面试 &gt;</div>
                    )}
                  </div>

                  {/* 展开历史 */}
                  {hasHistory && (
                    <>
                      <button
                        onClick={() => setExpandedJobId(expanded ? null : group.job_id)}
                        className="w-full text-center text-xs text-gray-400 hover:text-gray-600 py-2 border-t border-gray-100 transition-colors"
                      >
                        {expanded ? '收起历史' : '查看历史'}
                        <span className="ml-1">{expanded ? '▴' : '▾'}</span>
                      </button>
                      {expanded && (
                        <div className="border-t border-gray-100 px-2 py-1 space-y-0.5">
                          {group.history.map((iv) => (
                            <InterviewRow
                              key={iv.id}
                              iv={iv}
                              onClick={() => navigateInterview(iv)}
                            />
                          ))}
                        </div>
                      )}
                    </>
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
