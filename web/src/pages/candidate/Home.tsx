import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';
import type { Job } from '@/types';
import * as candidateApi from '@/api/candidate';

const statusLabels: Record<number, string> = {
  0: '待完善资料',
  1: '材料已提交',
  2: '面试中',
  3: '已完成',
  4: '已淘汰',
};

export default function Home() {
  const { candidate } = useCandidateStore();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    if (!candidate) return;
    candidateApi.getJobs().then((jobs) => setJobs(jobs));
  }, [candidate]);

  if (!candidate) return null;

  return (
    <div className="space-y-6 pb-20">
      {/* 欢迎卡片 */}
      <div className="bg-blue-600 text-white rounded-xl p-5">
        <p className="text-lg font-medium">
          {candidate.name ? `${candidate.name}，你好！` : '欢迎！'}
        </p>
        <p className="text-blue-100 text-sm mt-1">
          当前状态：{statusLabels[candidate.status] || '未知'}
        </p>
        {candidate.status === 0 && (
          <button
            onClick={() => navigate('/candidate/profile')}
            className="mt-3 bg-white text-blue-600 px-4 py-2 rounded-lg text-sm font-medium"
          >
            完善个人信息
          </button>
        )}
      </div>

      {/* 快捷操作 */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate('/candidate/profile')}
          className="bg-white rounded-xl p-4 shadow-sm text-center"
        >
          <div className="text-2xl mb-1">👤</div>
          <div className="text-sm text-gray-700">个人信息</div>
        </button>
        <button
          onClick={() => navigate('/candidate/documents')}
          className="bg-white rounded-xl p-4 shadow-sm text-center"
        >
          <div className="text-2xl mb-1">📄</div>
          <div className="text-sm text-gray-700">材料上传</div>
        </button>
        <button
          onClick={() => navigate('/candidate/interviews')}
          className="bg-white rounded-xl p-4 shadow-sm text-center"
        >
          <div className="text-2xl mb-1">🎤</div>
          <div className="text-sm text-gray-700">我的面试</div>
        </button>
        <div className="bg-white rounded-xl p-4 shadow-sm text-center opacity-50">
          <div className="text-2xl mb-1">📊</div>
          <div className="text-sm text-gray-700">面试报告</div>
        </div>
      </div>

      {/* 招聘岗位 */}
      {jobs.length > 0 && (
        <div>
          <h2 className="text-lg font-bold text-gray-800 mb-3">正在招聘</h2>
          <div className="space-y-3">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="bg-white rounded-xl p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => navigate(`/candidate/jobs/${job.id}`)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-800">{job.name}</h3>
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">{job.description}</p>
                  </div>
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full whitespace-nowrap">
                    招{job.quota}人
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
