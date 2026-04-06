import { create } from 'zustand';
import type { Candidate, Document } from '@/types';
import * as candidateApi from '@/api/candidate';

interface CandidateStore {
  candidate: Candidate | null;
  documents: Document[];
  loading: boolean;

  enterSystem: (phone: string) => Promise<void>;
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

  enterSystem: async (phone: string) => {
    set({ loading: true });
    try {
      const candidate = await candidateApi.enterSystem(phone);
      set({ candidate });
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

  reset: () => set({ candidate: null, documents: [], loading: false }),
}));
