import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';
import * as candidateApi from '@/api/candidate';
import type { Interview } from '@/types';

export default function InterviewResult() {
  const { interviewId: paramId } = useParams<{ interviewId: string }>();
  const navigate = useNavigate();
  const { candidate } = useCandidateStore();
  const interviewId = Number(paramId);

  const [interview, setInterview] = useState<Interview | null>(null);
  const [report, setReport] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!candidate) return;
    setLoading(true);
    candidateApi
      .getInterviewResult(candidate.id, interviewId)
      .then((res) => {
        setInterview(res.interview);
        setReport(res.report || '');
      })
      .catch((e) => setError(e instanceof Error ? e.message : '加载失败'))
      .finally(() => setLoading(false));
  }, [candidate, interviewId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500 text-lg">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-red-500">{error}</p>
        <button
          onClick={() => navigate('/candidate/interviews')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          返回面试列表
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部 */}
      <div className="bg-blue-600 text-white px-4 py-8 text-center">
        <h1 className="text-xl font-bold mb-2">面试结果</h1>
        <div className="text-2xl font-medium mb-1">感谢您完成面试</div>
        <div className="text-blue-100">我们将在3个工作日内通知您面试结果</div>
      </div>

      {/* 报告 */}
      <div className="max-w-lg mx-auto px-4 py-6">
        {report ? (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h2 className="font-bold text-gray-800 mb-3">面试报告</h2>
            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
              {report}
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-400 py-8">暂无详细报告</div>
        )}

        <button
          onClick={() => navigate('/candidate/interviews')}
          className="w-full mt-6 py-3 bg-blue-600 text-white text-lg font-medium rounded-xl hover:bg-blue-700 transition-colors"
        >
          返回面试列表
        </button>
      </div>
    </div>
  );
}
