import request from './request';
import type {
  ApiResponse, PaginatedData, DashboardStats,
  Job, JobCreate, Question, QuestionCreate,
  Candidate, Interview, InterviewDetail, SystemSettings, ScorePoolEntry,
} from '@/types';

// 登录
export async function hrLogin(username: string, password: string) {
  const res = await request.post<ApiResponse<{ access_token: string; display_name: string; role: string }>>('/hr/login', { username, password });
  return res.data.data;
}

// 仪表盘
export async function getDashboard() {
  const res = await request.get<ApiResponse<DashboardStats>>('/hr/dashboard');
  return res.data.data;
}

// 岗位
export async function getJobs(page = 1, pageSize = 20) {
  const res = await request.get<ApiResponse<PaginatedData<Job>>>('/hr/jobs', { params: { page, page_size: pageSize } });
  return res.data.data;
}

export async function getJob(id: number) {
  const res = await request.get<ApiResponse<Job>>(`/hr/jobs/${id}`);
  return res.data.data;
}

export async function createJob(data: JobCreate) {
  const res = await request.post<ApiResponse<Job>>('/hr/jobs', data);
  return res.data.data;
}

export async function updateJob(id: number, data: Partial<JobCreate>) {
  const res = await request.put<ApiResponse<Job>>(`/hr/jobs/${id}`, data);
  return res.data.data;
}

export async function deleteJob(id: number) {
  const res = await request.delete<ApiResponse<null>>(`/hr/jobs/${id}`);
  return res.data.data;
}

// 题目
export async function getQuestions(jobId: number) {
  const res = await request.get<ApiResponse<Question[]>>('/hr/questions', { params: { job_id: jobId } });
  return res.data.data;
}

export async function createQuestion(data: QuestionCreate) {
  const res = await request.post<ApiResponse<Question>>('/hr/questions', data);
  return res.data.data;
}

export async function updateQuestion(id: number, data: Partial<QuestionCreate>) {
  const res = await request.put<ApiResponse<Question>>(`/hr/questions/${id}`, data);
  return res.data.data;
}

export async function deleteQuestion(id: number) {
  const res = await request.delete<ApiResponse<null>>(`/hr/questions/${id}`);
  return res.data.data;
}

// 候选人
export async function getCandidates(page = 1, pageSize = 20, status?: number) {
  const res = await request.get<ApiResponse<PaginatedData<Candidate>>>('/hr/candidates', {
    params: { page, page_size: pageSize, status },
  });
  return res.data.data;
}

export async function inviteCandidate(candidateId: number, jobId: number) {
  const res = await request.post<ApiResponse<null>>(`/hr/candidates/${candidateId}/invite`, { job_id: jobId });
  return res.data.data;
}

// 面试记录
export async function getInterviews(page = 1, pageSize = 20) {
  const res = await request.get<ApiResponse<PaginatedData<Interview>>>('/hr/interviews', {
    params: { page, page_size: pageSize },
  });
  return res.data.data;
}

export async function getInterviewDetail(interviewId: number) {
  const res = await request.get<ApiResponse<InterviewDetail>>(`/hr/interviews/${interviewId}`);
  return res.data.data;
}

// 设置
export async function getSettings() {
  const res = await request.get<ApiResponse<SystemSettings>>('/hr/settings');
  return res.data.data;
}

export async function updateSettings(data: Record<string, string>) {
  const res = await request.put<ApiResponse<SystemSettings>>('/hr/settings', data);
  return res.data.data;
}

// 评分池
export async function getScorePool(jobId: number) {
  const res = await request.get<ApiResponse<ScorePoolEntry[]>>('/hr/score-pool', { params: { job_id: jobId } });
  return res.data.data;
}
