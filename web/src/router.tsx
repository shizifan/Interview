import { createBrowserRouter } from 'react-router-dom';
import CandidateLayout from '@/layouts/CandidateLayout';
import HRLayout from '@/layouts/HRLayout';

// 候选人端页面 - lazy import
import CandidateEnter from '@/pages/candidate/Enter';
import CandidateHome from '@/pages/candidate/Home';
import CandidateProfile from '@/pages/candidate/Profile';
import CandidateDocuments from '@/pages/candidate/Documents';
import CandidateInterviews from '@/pages/candidate/Interviews';
import InterviewRoom from '@/pages/candidate/InterviewRoom';
import InterviewResult from '@/pages/candidate/InterviewResult';

// HR端页面
import HRDashboard from '@/pages/hr/Dashboard';
import HRJobs from '@/pages/hr/Jobs';
import HRJobDetail from '@/pages/hr/JobDetail';
import HRCandidates from '@/pages/hr/Candidates';
import HRInterviews from '@/pages/hr/HRInterviews';
import HRScorePool from '@/pages/hr/ScorePool';
import HRSettings from '@/pages/hr/Settings';

export const router = createBrowserRouter([
  // 候选人入口（无布局）
  { path: '/', element: <CandidateEnter /> },

  // 候选人端
  {
    path: '/candidate',
    element: <CandidateLayout />,
    children: [
      { index: true, element: <CandidateHome /> },
      { path: 'profile', element: <CandidateProfile /> },
      { path: 'documents', element: <CandidateDocuments /> },
      { path: 'interviews', element: <CandidateInterviews /> },
    ],
  },
  // 面试间（全屏，无布局）
  { path: '/interview/:interviewId', element: <InterviewRoom /> },
  { path: '/interview/:interviewId/result', element: <InterviewResult /> },

  // HR端
  {
    path: '/hr',
    element: <HRLayout />,
    children: [
      { index: true, element: <HRDashboard /> },
      { path: 'jobs', element: <HRJobs /> },
      { path: 'jobs/:jobId', element: <HRJobDetail /> },
      { path: 'candidates', element: <HRCandidates /> },
      { path: 'interviews', element: <HRInterviews /> },
      { path: 'score-pool', element: <HRScorePool /> },
      { path: 'settings', element: <HRSettings /> },
    ],
  },
]);
