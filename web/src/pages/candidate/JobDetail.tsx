import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { Job } from '@/types';
import * as candidateApi from '@/api/candidate';

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    candidateApi
      .getJobs()
      .then((jobs) => {
        const found = jobs.find((j) => j.id === Number(jobId));
        setJob(found || null);
        if (!found) setError('岗位不存在或已关闭');
      })
      .catch(() => setError('加载失败'))
      .finally(() => setLoading(false));
  }, [jobId]);

  const handleApply = async () => {
    if (!job) return;
    setApplying(true);
    try {
      const state = await candidateApi.applyJob(job.id);
      navigate(`/interview/${state.interview_id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : '申请失败');
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-red-500">{error || '岗位不存在'}</p>
        <button
          onClick={() => navigate('/candidate')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          返回首页
        </button>
      </div>
    );
  }

  return (
    <div className="pb-24">
      {/* 岗位标题 */}
      <div className="bg-blue-600 text-white rounded-xl p-5 mb-4">
        <h1 className="text-xl font-bold">{job.name}</h1>
        <div className="flex items-center gap-3 mt-2 text-blue-100 text-sm">
          <span>招聘 {job.quota} 人</span>
        </div>
      </div>

      {/* 岗位描述 */}
      {job.description && (
        <div className="bg-white rounded-xl p-4 shadow-sm mb-3">
          <h2 className="font-bold text-gray-800 mb-2">岗位描述</h2>
          <p className="text-sm text-gray-600 whitespace-pre-wrap">{job.description}</p>
        </div>
      )}

      {/* 岗位要求 */}
      {job.requirements && (
        <div className="bg-white rounded-xl p-4 shadow-sm mb-3">
          <h2 className="font-bold text-gray-800 mb-2">任职要求</h2>
          <p className="text-sm text-gray-600 whitespace-pre-wrap">{job.requirements}</p>
        </div>
      )}

      {/* 底部按钮 */}
      <div className="fixed bottom-16 left-0 right-0 px-4">
        <div className="max-w-lg mx-auto flex gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex-1 py-3 bg-gray-100 text-gray-700 text-lg font-medium rounded-xl"
          >
            返回
          </button>
          <button
            onClick={handleApply}
            disabled={applying}
            className="flex-1 py-3 bg-blue-600 text-white text-lg font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {applying ? '申请中...' : '申请面试'}
          </button>
        </div>
      </div>
    </div>
  );
}
