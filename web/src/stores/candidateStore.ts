import { create } from 'zustand';
import type { Candidate, Document } from '@/types';
import * as candidateApi from '@/api/candidate';
import { useAuthStore } from './authStore';

interface CandidateStore {
  candidate: Candidate | null;
  documents: Document[];
  loading: boolean;
  initialized: boolean;

  init: () => Promise<void>;
  enterSystem: (phone: string, code: string) => Promise<void>;
  refreshProfile: () => Promise<void>;
  updateProfile: (data: Record<string, unknown>) => Promise<void>;
  loadDocuments: () => Promise<void>;
  uploadDocument: (file: File, docType: number) => Promise<void>;
  reset: () => void;
}

export const useCandidateStore = create<CandidateStore>((set, get) => ({
  candidate: null,
  documents: [],
  loading: false,
  initialized: false,

  init: async () => {
    const { candidate, initialized } = get();
    if (candidate || initialized) return;
    const auth = useAuthStore.getState();
    if (!auth.token || auth.role !== 'candidate') return;
    set({ loading: true, initialized: true });
    try {
      const me = await candidateApi.getMe();
      set({ candidate: me });
    } catch {
      auth.logout();
    } finally {
      set({ loading: false });
    }
  },

  enterSystem: async (phone: string, code: string) => {
    set({ loading: true });
    try {
      const data = await candidateApi.enterSystem(phone, code);
      useAuthStore.getState().setAuth(data.access_token, 'candidate');
      set({ candidate: data.candidate });
    } finally {
      set({ loading: false });
    }
  },

  refreshProfile: async () => {
    const { candidate } = get();
    if (!candidate) return;
    const updated = await candidateApi.getProfile(candidate.id);
    set({ candidate: updated });
  },

  updateProfile: async (data) => {
    const { candidate } = get();
    if (!candidate) return;
    const updated = await candidateApi.updateProfile(candidate.id, data);
    set({ candidate: updated });
  },

  loadDocuments: async () => {
    const { candidate } = get();
    if (!candidate) return;
    const docs = await candidateApi.listDocuments(candidate.id);
    set({ documents: docs });
  },

  uploadDocument: async (file: File, docType: number) => {
    const { candidate } = get();
    if (!candidate) return;
    await candidateApi.uploadDocument(candidate.id, file, docType);
    await get().loadDocuments();
  },

  reset: () => set({ candidate: null, documents: [], loading: false, initialized: false }),
}));
