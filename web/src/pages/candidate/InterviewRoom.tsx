import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useInterviewStore } from '@/stores/interviewStore';
import * as interviewApi from '@/api/interview';

/* ================================================================
 *  音频工具函数
 * ================================================================ */

/** 检测麦克风权限 */
async function checkMicPermission(): Promise<boolean> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    return true;
  } catch {
    return false;
  }
}

/** 播放 ArrayBuffer 音频 */
function playAudioBuffer(buffer: ArrayBuffer): Promise<void> {
  return new Promise((resolve, reject) => {
    const blob = new Blob([buffer], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
    audio.onerror = () => { URL.revokeObjectURL(url); reject(new Error('音频播放失败')); };
    audio.play().catch(reject);
  });
}

/* ================================================================
 *  设备检测页面
 * ================================================================ */

function DeviceCheck({ onReady }: { onReady: () => void }) {
  const [micOk, setMicOk] = useState<boolean | null>(null);
  const [netOk, setNetOk] = useState(navigator.onLine);

  useEffect(() => {
    checkMicPermission().then(setMicOk);
    const onOnline = () => setNetOk(true);
    const onOffline = () => setNetOk(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  const allOk = micOk === true && netOk;

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center px-6">
      <h2 className="text-2xl font-bold mb-8">设备检测</h2>

      <div className="w-full max-w-sm space-y-4 mb-8">
        <div className="flex items-center justify-between p-4 bg-gray-800 rounded-xl">
          <span className="text-lg">麦克风权限</span>
          {micOk === null ? (
            <span className="text-gray-400">检测中...</span>
          ) : micOk ? (
            <span className="text-green-400 text-xl">✓</span>
          ) : (
            <span className="text-red-400 text-xl">✗</span>
          )}
        </div>
        <div className="flex items-center justify-between p-4 bg-gray-800 rounded-xl">
          <span className="text-lg">网络连接</span>
          {netOk ? (
            <span className="text-green-400 text-xl">✓</span>
          ) : (
            <span className="text-red-400 text-xl">✗</span>
          )}
        </div>
      </div>

      {!micOk && micOk !== null && (
        <p className="text-red-400 text-sm mb-4 text-center">
          请允许浏览器使用麦克风，或在浏览器设置中启用麦克风权限后刷新页面
        </p>
      )}
      {!netOk && (
        <p className="text-red-400 text-sm mb-4 text-center">
          网络连接异常，请检查网络后重试
        </p>
      )}

      <button
        onClick={onReady}
        disabled={!allOk}
        className="px-8 py-4 bg-blue-600 rounded-xl text-lg font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        开始面试
      </button>
    </div>
  );
}

/* ================================================================
 *  音频格式转换工具
 * ================================================================ */

/** 将任意浏览器录音 Blob 转为 16-bit PCM WAV（兼容 DashScope ASR） */
async function convertBlobToWav(blob: Blob): Promise<ArrayBuffer> {
  const arrayBuffer = await blob.arrayBuffer();
  const audioCtx = new AudioContext();
  try {
    const decoded = await audioCtx.decodeAudioData(arrayBuffer);
    const pcm = decoded.getChannelData(0); // mono
    return encodeWav(pcm, decoded.sampleRate);
  } finally {
    audioCtx.close();
  }
}

function encodeWav(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const dataSize = samples.length * 2; // 16-bit = 2 bytes per sample
  const buffer = new ArrayBuffer(44 + dataSize);
  const v = new DataView(buffer);
  const w = (off: number, s: string) => { for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); };
  w(0, 'RIFF'); v.setUint32(4, 36 + dataSize, true); w(8, 'WAVE');
  w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, 1, true); v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  w(36, 'data'); v.setUint32(40, dataSize, true);
  let off = 44;
  for (let i = 0; i < samples.length; i++, off += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  return buffer;
}

/* ================================================================
 *  录音 Hook
 * ================================================================ */

function useRecorder() {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const { sendAudio, sendAudioEnd, setRecording } = useInterviewStore();

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // 优先使用 webm/opus，fallback 到浏览器默认
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : '';
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      if (chunksRef.current.length > 0) {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        // 将 WebM/Opus 转为 WAV 以兼容 DashScope ASR
        const wavBuffer = await convertBlobToWav(blob);
        sendAudio(wavBuffer);
      }
      sendAudioEnd();
      setRecording(false);
    };

    recorderRef.current = recorder;
    recorder.start(250); // 每 250ms 触发一次 dataavailable
    setRecording(true);
  }, [sendAudio, sendAudioEnd, setRecording]);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  }, []);

  return { startRecording, stopRecording };
}

/* ================================================================
 *  TTS 播放 Hook
 * ================================================================ */

function useTtsPlayer() {
  const { consumeTtsAudio, setTtsPlaying, sendMessage } = useInterviewStore();

  const playNext = useCallback(async () => {
    const buffer = consumeTtsAudio();
    if (!buffer) return;

    setTtsPlaying(true);
    try {
      await playAudioBuffer(buffer);
    } catch {
      // 播放失败静默处理
    } finally {
      setTtsPlaying(false);
      sendMessage({ type: 'tts_played', data: {} });
    }
  }, [consumeTtsAudio, setTtsPlaying, sendMessage]);

  return { playNext };
}

/* ================================================================
 *  InterviewRoom 主组件
 * ================================================================ */

export default function InterviewRoom() {
  const { interviewId: paramId } = useParams<{ interviewId: string }>();
  const navigate = useNavigate();
  const {
    state, loading, connected, connectWs, disconnect,
    submitAnswer, handleTimeout, abort,
    isRecording, isTtsPlaying, asrText, ttsAudioQueue,
    reconnecting, reconnectAttempt,
  } = useInterviewStore();

  const [deviceReady, setDeviceReady] = useState(false);
  const [answerText, setAnswerText] = useState('');
  const [timeLeft, setTimeLeft] = useState(30);
  const [submitting, setSubmitting] = useState(false);
  const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
  const timerRef = useRef<ReturnType<typeof setInterval>>(null);
  const interviewId = Number(paramId);

  const { startRecording, stopRecording } = useRecorder();
  const { playNext } = useTtsPlayer();

  // 初始化：加载面试状态 & 连接 WebSocket
  useEffect(() => {
    if (!interviewId || !deviceReady) return;
    interviewApi.getInterviewState(interviewId).then((s) => {
      useInterviewStore.setState({ state: s, interviewId });
    }).catch(() => {
      interviewApi.recoverInterview(interviewId).then((s) => {
        useInterviewStore.setState({ state: s, interviewId });
      }).catch(() => navigate('/candidate/interviews'));
    });
    connectWs(interviewId);
    return () => disconnect();
  }, [interviewId, deviceReady, connectWs, disconnect, navigate]);

  // TTS 音频到达时自动播放
  useEffect(() => {
    if (ttsAudioQueue.length > 0 && !isTtsPlaying) {
      playNext();
    }
  }, [ttsAudioQueue.length, isTtsPlaying, playNext]);

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

  // 当节点变为 wait_asr 时启动倒计时（监听多个状态变化以处理重试/新题目等场景）
  const [timerKey, setTimerKey] = useState(0);

  useEffect(() => {
    if (state?.current_node === 'wait_asr') {
      setTimerKey(k => k + 1);
      resetTimer();
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [state?.current_node, state?.message, resetTimer]);

  // 面试结束自动跳转
  useEffect(() => {
    if (state?.status === 'completed' || state?.status === 'interrupted') {
      setTimeout(() => navigate(`/interview/${interviewId}/result`), 3000);
    }
  }, [state?.status, interviewId, navigate]);

  const handleSubmitText = async () => {
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

  // 设备检测页
  if (!deviceReady) {
    return <DeviceCheck onReady={() => setDeviceReady(true)} />;
  }

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
      {/* 断连恢复横幅 */}
      {reconnecting && (
        <div className="bg-yellow-600 text-center py-2 text-sm font-medium animate-pulse">
          连接中断，正在重连 ({reconnectAttempt}/5)...
        </div>
      )}
      {!connected && !reconnecting && !isFinished && state && (
        <div className="bg-red-600 text-center py-2 text-sm font-medium">
          连接已断开，请检查网络后刷新页面
        </div>
      )}

      {/* 顶部状态栏 */}
      <header className="flex justify-between items-center px-4 py-3 bg-gray-800">
        <div className="text-sm">
          {state ? `第 ${(state.current_question_index ?? 0) + 1} / ${state.total_questions ?? 0} 题` : '面试'}
        </div>
        <div className="flex items-center gap-3">
          {/* 连接状态 */}
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
          {isWaiting && (
            <span className={`text-lg font-bold ${timeLeft <= 10 ? 'text-red-400' : 'text-green-400'}`}>
              {timeLeft}s
            </span>
          )}
        </div>
        <button onClick={handleAbort} className="text-sm text-red-400 hover:text-red-300">
          退出面试
        </button>
      </header>

      {/* TTS 播报区域 */}
      <div className="flex-1 flex flex-col items-center justify-center px-6">
        {/* AI 头像 */}
        <div className={`w-24 h-24 rounded-full flex items-center justify-center text-4xl mb-6 transition-colors ${
          isTtsPlaying ? 'bg-blue-500 animate-pulse' : 'bg-blue-600'
        }`}>
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
          {isTtsPlaying && (
            <p className="text-sm text-blue-400 mt-2">语音播报中...</p>
          )}
        </div>

        {/* ASR 识别结果 */}
        {asrText && isWaiting && (
          <div className="mt-4 px-4 py-2 bg-gray-800 rounded-lg max-w-md">
            <p className="text-sm text-gray-400">语音识别：</p>
            <p className="text-base">{asrText}</p>
          </div>
        )}

        {/* 面试结束 */}
        {isFinished && (
          <div className="mt-8 text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">
              面试完成
            </div>
            <p className="text-gray-400">正在跳转到结果页...</p>
          </div>
        )}
      </div>

      {/* 底部操作区 */}
      {!isFinished && (
        <div className="px-4 py-4 bg-gray-800 border-t border-gray-700">
          {/* 模式切换 */}
          <div className="flex justify-center gap-4 mb-3">
            <button
              onClick={() => setInputMode('voice')}
              className={`text-xs px-3 py-1 rounded-full ${inputMode === 'voice' ? 'bg-blue-600' : 'bg-gray-700 text-gray-400'}`}
            >
              语音回答
            </button>
            <button
              onClick={() => setInputMode('text')}
              className={`text-xs px-3 py-1 rounded-full ${inputMode === 'text' ? 'bg-blue-600' : 'bg-gray-700 text-gray-400'}`}
            >
              文字回答
            </button>
          </div>

          {inputMode === 'voice' ? (
            /* 语音模式 */
            <div className="flex justify-center">
              {isRecording ? (
                <button
                  onClick={stopRecording}
                  disabled={!isWaiting}
                  className="w-20 h-20 rounded-full bg-red-500 flex items-center justify-center text-3xl hover:bg-red-600 active:scale-95 transition-all animate-pulse disabled:opacity-50"
                >
                  ■
                </button>
              ) : (
                <button
                  onClick={startRecording}
                  disabled={!isWaiting || isTtsPlaying}
                  className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center text-3xl hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  🎤
                </button>
              )}
            </div>
          ) : (
            /* 文字模式 */
            <div className="flex gap-2">
              <input
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmitText()}
                placeholder={isWaiting ? '请输入您的回答...' : '等待出题...'}
                disabled={!isWaiting || submitting}
                className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white text-base placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              />
              <button
                onClick={handleSubmitText}
                disabled={!isWaiting || submitting || !answerText.trim()}
                className="px-6 py-3 bg-blue-600 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {submitting ? '...' : '发送'}
              </button>
            </div>
          )}

          {isRecording && (
            <p className="text-center text-sm text-red-400 mt-2 animate-pulse">
              录音中，点击停止按钮结束回答
            </p>
          )}
        </div>
      )}
    </div>
  );
}
