import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useInterviewStore } from '@/stores/interviewStore';
import * as interviewApi from '@/api/interview';

export default function InterviewRoom() {
  const { interviewId: paramId } = useParams<{ interviewId: string }>();
  const navigate = useNavigate();
  const {
    state, loading, connectWs, disconnect, submitAnswer, handleTimeout, abort,
  } = useInterviewStore();

  const [answerText, setAnswerText] = useState('');
  const [timeLeft, setTimeLeft] = useState(30);
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval>>(null);
  const interviewId = Number(paramId);

  // 初始化：加载面试状态 & 连接 WebSocket
  useEffect(() => {
    if (!interviewId) return;
    interviewApi.getInterviewState(interviewId).then((s) => {
      useInterviewStore.setState({ state: s, interviewId });
    }).catch(() => {
      // 尝试恢复
      interviewApi.recoverInterview(interviewId).then((s) => {
        useInterviewStore.setState({ state: s, interviewId });
      }).catch(() => navigate('/candidate/interviews'));
    });
    connectWs(interviewId);
    return () => disconnect();
  }, [interviewId, connectWs, disconnect, navigate]);

  // 倒计时
  const resetTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setTimeLeft(30);
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          handleTimeout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [handleTimeout]);

  // 当节点变为 wait_asr 时启动倒计时
  useEffect(() => {
    if (state?.current_node === 'wait_asr') {
      resetTimer();
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [state?.current_node, resetTimer]);

  // 面试结束自动跳转
  useEffect(() => {
    if (state?.status === 'completed' || state?.status === 'interrupted') {
      setTimeout(() => navigate(`/interview/${interviewId}/result`), 2000);
    }
  }, [state?.status, interviewId, navigate]);

  const handleSubmitAnswer = async () => {
    if (!answerText.trim()) return;
    setSubmitting(true);
    try {
      await submitAnswer(answerText.trim());
      setAnswerText('');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAbort = async () => {
    if (confirm('确定要中断面试吗？进度将被保存。')) {
      await abort();
      navigate('/candidate/interviews');
    }
  };

  if (loading && !state) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-lg">加载面试中...</div>
      </div>
    );
  }

  const isWaiting = state?.current_node === 'wait_asr';
  const isFinished = state?.status === 'completed' || state?.status === 'interrupted';

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {/* 顶部状态栏 */}
      <header className="flex justify-between items-center px-4 py-3 bg-gray-800">
        <div className="text-sm">
          {state ? `第 ${(state.current_question_index ?? 0) + 1} / ${state.total_questions ?? 0} 题` : '面试'}
        </div>
        {isWaiting && (
          <div className={`text-lg font-bold ${timeLeft <= 10 ? 'text-red-400' : 'text-green-400'}`}>
            {timeLeft}s
          </div>
        )}
        <button onClick={handleAbort} className="text-sm text-red-400 hover:text-red-300">
          退出面试
        </button>
      </header>

      {/* TTS 播报区域 */}
      <div className="flex-1 flex flex-col items-center justify-center px-6">
        {/* AI 头像 */}
        <div className="w-24 h-24 rounded-full bg-blue-600 flex items-center justify-center text-4xl mb-6">
          AI
        </div>

        {/* 消息/题目文本 */}
        <div className="text-center max-w-md">
          {state?.tts_text && (
            <p className="text-xl leading-relaxed mb-4">{state.tts_text}</p>
          )}
          {state?.message && (
            <p className="text-sm text-gray-400">{state.message}</p>
          )}
        </div>

        {/* 面试结束 */}
        {isFinished && (
          <div className="mt-8 text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">
              {state?.score ?? 0}分
            </div>
            <p className="text-gray-400">正在跳转到结果页...</p>
          </div>
        )}
      </div>

      {/* 底部输入区（MVP: 文字输入代替语音） */}
      {!isFinished && (
        <div className="px-4 py-4 bg-gray-800 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-2 text-center">
            MVP模式：请用文字输入回答（正式版将支持语音）
          </p>
          <div className="flex gap-2">
            <input
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmitAnswer()}
              placeholder={isWaiting ? '请输入您的回答...' : '等待出题...'}
              disabled={!isWaiting || submitting}
              className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white text-base placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={handleSubmitAnswer}
              disabled={!isWaiting || submitting || !answerText.trim()}
              className="px-6 py-3 bg-blue-600 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? '...' : '发送'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
