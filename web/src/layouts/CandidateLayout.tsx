import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/candidate', label: '首页' },
  { path: '/candidate/profile', label: '个人信息' },
  { path: '/candidate/documents', label: '材料上传' },
  { path: '/candidate/interviews', label: '我的面试' },
];

export default function CandidateLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <h1
            className="text-lg font-bold text-blue-600 cursor-pointer"
            onClick={() => navigate('/candidate')}
          >
            AI面试官
          </h1>
        </div>
      </header>

      {/* 内容区 */}
      <main className="max-w-lg mx-auto px-4 py-4">
        <Outlet />
      </main>

      {/* 底部导航 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-10">
        <div className="max-w-lg mx-auto flex">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex-1 py-3 text-center text-sm transition-colors ${
                  isActive
                    ? 'text-blue-600 font-medium'
                    : 'text-gray-500'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
