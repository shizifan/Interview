import { create } from 'zustand';
import type { InterviewState, WsMessage } from '@/types';
import * as interviewApi from '@/api/interview';

interface InterviewStore {
  interviewId: number | null;
  state: InterviewState | null;
  ws: WebSocket | null;
  connected: boolean;
  loading: boolean;

  startInterview: (candidateId: number, jobId: number) => Promise<void>;
  recoverInterview: (interviewId: number) => Promise<void>;
  connectWs: (interviewId: number) => void;
  sendMessage: (msg: WsMessage) => void;
  submitAnswer: (text: string) => Promise<void>;
  handleTimeout: () => Promise<void>;
  abort: () => Promise<void>;
  disconnect: () => void;
  reset: () => void;
}

export const useInterviewStore = create<InterviewStore>((set, get) => ({
  interviewId: null,
  state: null,
  ws: null,
  connected: false,
  loading: false,

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
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/interview/${interviewId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => set({ connected: true });

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage;
        if (msg.type === 'state_update' || msg.type === 'interview_end') {
          set({ state: msg.data as unknown as InterviewState });
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => set({ connected: false, ws: null });
    ws.onerror = () => set({ connected: false });

    set({ ws, interviewId });
  },

  sendMessage: (msg) => {
    const { ws, connected } = get();
    if (ws && connected) {
      ws.send(JSON.stringify(msg));
    }
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
    const { ws } = get();
    if (ws) {
      ws.close();
    }
    set({ ws: null, connected: false });
  },

  reset: () => {
    get().disconnect();
    set({ interviewId: null, state: null, loading: false });
  },
}));
