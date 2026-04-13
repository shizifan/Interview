/* ========== 通用 ========== */
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/* ========== 候选人 ========== */
export interface Candidate {
  id: number;
  name: string;
  phone: string;
  id_card: string | null;
  gender: number;
  age: number | null;
  education: string | null;
  work_experience: number;
  address: string | null;
  status: number; // 0=待完善 1=材料已提交 2=面试中 3=已完成 4=已淘汰
  total_score: number;
  created_at: string;
}

export interface CandidateProfileUpdate {
  name?: string;
  gender?: number;
  age?: number;
  education?: string;
  work_experience?: number;
  address?: string;
}

/* ========== 材料 ========== */
export interface Document {
  id: number;
  candidate_id: number;
  type: number; // 1=身份证 2=驾驶证 3=从业资格证 4=体检报告
  file_path: string;
  ocr_result: Record<string, string> | null;
  score: number;
  status: number;
  created_at: string;
}

/* ========== 岗位 ========== */
export interface Job {
  id: number;
  name: string;
  description: string;
  requirements: string;
  quota: number;
  start_coefficient: number;
  min_interview_count: number;
  required_license_type: string;
  status: number; // 0=草稿 1=招聘中 2=已关闭
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  name: string;
  description: string;
  requirements: string;
  quota: number;
  start_coefficient?: number;
  min_interview_count?: number;
  required_license_type?: string;
}

/* ========== 题目 ========== */
export interface Question {
  id: number;
  job_id: number;
  content: string;
  question_type: number;
  sort_order: number;
  score_points: string[];
  follow_up_scripts: string[];
  is_active: boolean;
  created_at: string;
}

export interface QuestionCreate {
  job_id: number;
  content: string;
  question_type?: number;
  sort_order?: number;
  score_points?: string[];
  follow_up_scripts?: string[];
}

/* ========== 面试 ========== */
export interface Interview {
  id: number;
  candidate_id: number;
  job_id: number;
  status: number; // 0=待开始 1=进行中 2=已完成 3=已中断 4=已过期
  current_node: string;
  total_score: number;
  report_content: string | null;
  created_at: string;
  updated_at: string;
}

export interface InterviewAnswer {
  id: number;
  interview_id: number;
  question_id: number;
  question_order: number;
  answer_text: string;
  follow_up_count: number;
  score: number;
  score_detail: string | null;
}

export interface InterviewDetail {
  interview: Interview;
  answers: InterviewAnswer[];
  candidate_name: string | null;
  job_name: string | null;
}

/* ========== 面试状态机 ========== */
export interface InterviewState {
  interview_id: number;
  current_node: string;
  current_question_index: number;
  total_questions: number;
  tts_text: string | null;
  status: string;
  score: number;
  message: string | null;
}

export interface WsMessage {
  type: string;
  data: Record<string, unknown>;
}

/* ========== HR 仪表盘 ========== */
export interface DashboardStats {
  today_interviews: number;
  completed_interviews: number;
  pass_rate: number;
  pending_documents: number;
  total_candidates: number;
}

/* ========== 评分池 ========== */
export interface ScorePoolEntry {
  id: number;
  candidate_id: number;
  job_id: number;
  candidate_name: string;
  candidate_phone: string;
  doc_score: number;
  interview_score: number;
  total_score: number;
  rank: number | null;
  is_invited: boolean;
}

/* ========== 系统设置 ========== */
export interface SystemSettings {
  [key: string]: {
    value: string;
    description: string;
  };
}
