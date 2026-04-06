import request from './request';
import type { ApiResponse, Candidate, CandidateProfileUpdate, Document, Interview } from '@/types';

export async function enterSystem(phone: string, code: string) {
  const res = await request.post<ApiResponse<{ access_token: string; candidate: Candidate }>>('/candidate/enter', { phone, code });
  return res.data.data;
}

export async function getProfile(candidateId: number) {
  const res = await request.get<ApiResponse<Candidate>>(`/candidate/candidates/${candidateId}/profile`);
  return res.data.data;
}

export async function updateProfile(candidateId: number, data: CandidateProfileUpdate) {
  const res = await request.put<ApiResponse<Candidate>>(`/candidate/candidates/${candidateId}/profile`, data);
  return res.data.data;
}

export async function uploadDocument(candidateId: number, file: File, docType: number) {
  const form = new FormData();
  form.append('file', file);
  form.append('doc_type', String(docType));
  const res = await request.post<ApiResponse<Document>>(`/candidate/candidates/${candidateId}/documents`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data.data;
}

export async function listDocuments(candidateId: number) {
  const res = await request.get<ApiResponse<Document[]>>(`/candidate/candidates/${candidateId}/documents`);
  return res.data.data;
}

export async function listInterviews(candidateId: number) {
  const res = await request.get<ApiResponse<Interview[]>>(`/candidate/candidates/${candidateId}/interviews`);
  return res.data.data;
}

export async function getInterviewResult(candidateId: number, interviewId: number) {
  const res = await request.get<ApiResponse<{ interview: Interview; report: string }>>(
    `/candidate/candidates/${candidateId}/interviews/${interviewId}/result`,
  );
  return res.data.data;
}

export async function confirmOcr(candidateId: number, documentId: number, correctedFields: Record<string, string>) {
  const res = await request.put<ApiResponse<Document>>(
    `/candidate/candidates/${candidateId}/documents/${documentId}/ocr`,
    { corrected_fields: correctedFields },
  );
  return res.data.data;
}
