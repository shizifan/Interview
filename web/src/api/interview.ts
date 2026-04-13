import request from './request';
import type { ApiResponse, InterviewState } from '@/types';

export async function getInterviewState(interviewId: number) {
  const res = await request.get<ApiResponse<InterviewState>>(`/interview/${interviewId}/state`);
  return res.data.data;
}

export async function startInterview(candidateId: number, jobId: number) {
  const res = await request.post<ApiResponse<InterviewState>>('/interview/start', {
    candidate_id: candidateId,
    job_id: jobId,
  });
  return res.data.data;
}

export async function recoverInterview(interviewId: number) {
  const res = await request.post<ApiResponse<InterviewState>>(`/interview/${interviewId}/recover`);
  return res.data.data;
}

export async function submitAnswer(interviewId: number, answerText: string) {
  const res = await request.post<ApiResponse<InterviewState>>(`/interview/${interviewId}/submit-answer`, {
    answer_text: answerText,
  });
  return res.data.data;
}

export async function reportTimeout(interviewId: number) {
  const res = await request.post<ApiResponse<InterviewState>>(`/interview/${interviewId}/timeout`);
  return res.data.data;
}

export async function abortInterview(interviewId: number) {
  const res = await request.post<ApiResponse<InterviewState>>(`/interview/${interviewId}/abort`);
  return res.data.data;
}
