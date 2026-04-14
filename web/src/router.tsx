import { useEffect } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import CandidateLayout from '@/layouts/CandidateLayout';
import HRLayout from '@/layouts/HRLayout';
import { useAuthStore } from '@/stores/authStore';
import { useCandidateStore } from '@/stores/candidateStore';

// 候选人端页面
import CandidateEnter from '@/pages/candidate/Enter';
import CandidateHome from '@/pages/candidate/Home';
import CandidateProfile from '@/pages/candidate/Profile';
import CandidateDocuments from '@/pages/candidate/Documents';
import CandidateInterviews from '@/pages/candidate/Interviews';
import CandidateJobDetail from '@/pages/candidate/JobDetail';
import InterviewRoom from '@/pages/candidate/InterviewRoom';
import InterviewResult from '@/pages/candidate/InterviewResult';

// 测试页面
import TestInterview from '@/pages/test/TestInterview';

// HR端页面
import HRLogin from '@/pages/hr/Login';
import HRDashboard from '@/pages/hr/Dashboard';
import HRJobs from '@/pages/hr/Jobs';
import HRJobDetail from '@/pages/hr/JobDetail';
import HRCandidates from '@/pages/hr/Candidates';
import HRCandidateDetail from '@/pages/hr/CandidateDetail';
import HRInterviews from '@/pages/hr/HRInterviews';
import HRScorePool from '@/pages/hr/ScorePool';
import HRSettings from '@/pages/hr/Settings';

function RequireCandidateAuth({ children }: { children: React.ReactNode }) {
  const { token, role } = useAuthStore();
  const init = useCandidateStore((s) => s.init);
  const loading = useCandidateStore((s) => s.loading);
  const candidate = useCandidateStore((s) => s.candidate);

  useEffect(() => {
    init();
  }, [init]);

  if (!token || role !== 'candidate') return <Navigate to="/" replace />;

  if (loading && !candidate) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  return <>{children}</>;
}

function RequireHRAuth({ children }: { children: React.ReactNode }) {
  const { token, role } = useAuthStore();
  if (!token || role !== 'hr') return <Navigate to="/hr/login" replace />;
  return <>{children}</>;
}

export const router = createBrowserRouter([
  // 候选人入口（无需认证）
  { path: '/', element: <CandidateEnter /> },

  // 测试路由（无需认证）
  { path: '/test/interview', element: <TestInterview /> },
  { path: '/test/room/:interviewId', element: <InterviewRoom /> },

  // 候选人端（需要候选人认证）
  {
    path: '/candidate',
    element: <RequireCandidateAuth><CandidateLayout /></RequireCandidateAuth>,
    children: [
      { index: true, element: <CandidateHome /> },
      { path: 'profile', element: <CandidateProfile /> },
      { path: 'documents', element: <CandidateDocuments /> },
      { path: 'interviews', element: <CandidateInterviews /> },
      { path: 'jobs/:jobId', element: <CandidateJobDetail /> },
    ],
  },
  // 面试间（需要候选人认证）
  { path: '/interview/:interviewId', element: <RequireCandidateAuth><InterviewRoom /></RequireCandidateAuth> },
  { path: '/interview/:interviewId/result', element: <RequireCandidateAuth><InterviewResult /></RequireCandidateAuth> },

  // HR 登录（无需认证）
  { path: '/hr/login', element: <HRLogin /> },

  // HR端（需要HR认证）
  {
    path: '/hr',
    element: <RequireHRAuth><HRLayout /></RequireHRAuth>,
    children: [
      { index: true, element: <HRDashboard /> },
      { path: 'jobs', element: <HRJobs /> },
      { path: 'jobs/:jobId', element: <HRJobDetail /> },
      { path: 'candidates', element: <HRCandidates /> },
      { path: 'candidates/:candidateId', element: <HRCandidateDetail /> },
      { path: 'interviews', element: <HRInterviews /> },
      { path: 'score-pool', element: <HRScorePool /> },
      { path: 'settings', element: <HRSettings /> },
    ],
  },
]);
