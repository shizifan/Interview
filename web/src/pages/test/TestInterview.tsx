import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '@/api/request';

export default function TestInterview() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await request.post('/test/quick-start');
      const { interview_id } = res.data.data;
      navigate(`/test/room/${interview_id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '启动失败，请检查后端服务');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center px-6">
      <h1 className="text-3xl font-bold mb-4">面试链路快速测试</h1>
      <p className="text-gray-400 text-center max-w-md mb-2">
        跳过登录，直接创建测试面试并进入面试间。
      </p>
      <p className="text-gray-500 text-center max-w-md mb-8 text-sm">
        使用种子数据中的「卡车司机」岗位（5 道题），验证完整链路：
        浏览器录音 → ASR 识别 → LLM 评分 → TTS 播放。
      </p>

      {error && (
        <div className="mb-6 px-4 py-3 bg-red-900/50 border border-red-700 rounded-xl text-red-300 text-sm max-w-md text-center">
          {error}
        </div>
      )}

      <button
        onClick={handleStart}
        disabled={loading}
        className="px-8 py-4 bg-blue-600 rounded-xl text-lg font-medium hover:bg-blue-700 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        {loading ? '创建面试中...' : '开始测试面试'}
      </button>

      <div className="mt-12 text-gray-600 text-xs max-w-md text-center space-y-1">
        <p>确保 .env 中 AI_SERVICE_MODE=real 且 DASHSCOPE_API_KEY 已配置</p>
        <p>如使用 mock 模式，ASR/TTS/LLM 将返回预定义结果</p>
      </div>
    </div>
  );
}
