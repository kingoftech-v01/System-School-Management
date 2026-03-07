import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/stores/auth';

export function Sidebar() {
  const location = useLocation();
  const user = useAuthStore((s) => s.user);

  const { data: navData } = useQuery({
    queryKey: ['navigation'],
    queryFn: authApi.getNavigation,
    staleTime: 10 * 60 * 1000,
  });

  const navItems = navData?.navigation ?? [];

  return (
    <aside className="w-64 min-h-screen bg-slate-900 text-white flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl font-bold">Aurelius</h1>
        <p className="text-sm text-slate-400 mt-1 capitalize">{user?.role} Portal</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <span className="w-5 text-center">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-medium">
            {user?.first_name?.[0] || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
