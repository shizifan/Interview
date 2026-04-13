import { create } from 'zustand';
import type { InterviewState, WsMessage } from '@/types';
import * as interviewApi from '@/api/interview';

interface InterviewStore {
  interviewId: number | null;
  state: InterviewState | null;
  ws: WebSocket | null;
  connected: boolean;
  loading: boolean;
  // 音频相关
  isRecording: boolean;
  isTtsPlaying: boolean;
  asrText: string | null;
  ttsAudioQueue: ArrayBuffer[];
  // 重连相关
  reconnecting: boolean;
  reconnectAttempt: number;
  _reconnectTimer: ReturnType<typeof setTimeout> | null;

  startInterview: (candidateId: number, jobId: number) => Promise<void>;
  recoverInterview: (interviewId: number) => Promise<void>;
  connectWs: (interviewId: number) => void;
  sendMessage: (msg: WsMessage) => void;
  sendAudio: (audioData: ArrayBuffer) => void;
  sendAudioEnd: () => void;
  submitAnswer: (text: string) => Promise<void>;
  handleTimeout: () => Promise<void>;
  abort: () => Promise<void>;
  disconnect: () => void;
  reset: () => void;
  setRecording: (v: boolean) => void;
  setTtsPlaying: (v: boolean) => void;
  consumeTtsAudio: () => ArrayBuffer | undefined;
}

const MAX_RECONNECT_ATTEMPTS = 5;

export const useInterviewStore = create<InterviewStore>((set, get) => ({
  interviewId: null,
  state: null,
  ws: null,
  connected: false,
  loading: false,
  isRecording: false,
  isTtsPlaying: false,
  asrText: null,
  ttsAudioQueue: [],
  reconnecting: false,
  reconnectAttempt: 0,
  _reconnectTimer: null,

  startInterview: async (candidateId, jobId) => {
    set({ loading: true });
    try {
      const state = await interviewApi.startInterview(candidateId, jobId);
      set({ interviewId: state.interview_id, state });
    } finally {
      set({ loading: false });
    }
  },

  recoverInterview: async (interviewId) => {
    set({ loading: true });
    try {
      const state = await interviewApi.recoverInterview(interviewId);
      set({ interviewId, state });
    } finally {
      set({ loading: false });
    }
  },

  connectWs: (interviewId) => {
    // 清理之前的重连定时器
    const oldTimer = get()._reconnectTimer;
    if (oldTimer) clearTimeout(oldTimer);

    const token = localStorage.getItem('token') || '';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/interview/${interviewId}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => set({ connected: true, reconnecting: false, reconnectAttempt: 0 });

    ws.onmessage = (event) => {
      // 二进制消息 = TTS 音频
      if (event.data instanceof ArrayBuffer) {
        set((s) => ({ ttsAudioQueue: [...s.ttsAudioQueue, event.data as ArrayBuffer] }));
        return;
      }
      // JSON 消息
      try {
        const msg = JSON.parse(event.data) as WsMessage;
        if (msg.type === 'state_update' || msg.type === 'interview_end') {
          set({ state: msg.data as unknown as InterviewState });
        } else if (msg.type === 'asr_result') {
          set({ asrText: (msg.data as { text: string }).text });
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      set({ connected: false, ws: null });
      // 自动重连（面试未结束时）
      const { state: currentState, reconnectAttempt } = get();
      const isFinished = currentState?.status === 'completed' || currentState?.status === 'interrupted';
      if (!isFinished && reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 16000);
        set({ reconnecting: true, reconnectAttempt: reconnectAttempt + 1 });
        const timer = setTimeout(() => get().connectWs(interviewId), delay);
        set({ _reconnectTimer: timer });
      } else if (reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) {
        set({ reconnecting: false });
      }
    };

    ws.onerror = () => set({ connected: false });

    set({ ws, interviewId });
  },

  sendMessage: (msg) => {
    const { ws, connected } = get();
    if (ws && connected && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  },

  sendAudio: (audioData) => {
    const { ws, connected } = get();
    if (ws && connected && ws.readyState === WebSocket.OPEN) {
      ws.send(audioData);
    }
  },

  sendAudioEnd: () => {
    get().sendMessage({ type: 'audio_end', data: {} });
  },

  submitAnswer: async (text) => {
    const { interviewId } = get();
    if (!interviewId) return;
    set({ loading: true });
    try {
      const state = await interviewApi.submitAnswer(interviewId, text);
      set({ state });
    } finally {
      set({ loading: false });
    }
  },

  handleTimeout: async () => {
    const { interviewId } = get();
    if (!interviewId) return;
    const state = await interviewApi.reportTimeout(interviewId);
    set({ state });
  },

  abort: async () => {
    const { interviewId } = get();
    if (!interviewId) return;
    const state = await interviewApi.abortInterview(interviewId);
    set({ state });
    get().disconnect();
  },

  disconnect: () => {
    const { ws, _reconnectTimer } = get();
    if (_reconnectTimer) clearTimeout(_reconnectTimer);
    if (ws) {
      ws.close();
    }
    set({ ws: null, connected: false, reconnecting: false, reconnectAttempt: 0, _reconnectTimer: null });
  },

  reset: () => {
    get().disconnect();
    set({
      interviewId: null, state: null, loading: false,
      isRecording: false, isTtsPlaying: false, asrText: null, ttsAudioQueue: [],
    });
  },

  setRecording: (v) => set({ isRecording: v }),
  setTtsPlaying: (v) => set({ isTtsPlaying: v }),
  consumeTtsAudio: () => {
    const queue = get().ttsAudioQueue;
    if (queue.length === 0) return undefined;
    const first = queue[0];
    set({ ttsAudioQueue: queue.slice(1) });
    return first;
  },
}));
