import { useAuthStore } from '@/stores/auth';
import { useAuth } from '@/hooks/useAuth';

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            Welcome, {user?.first_name || 'User'}
          </h1>
          <p className="text-slate-500 mt-1 capitalize">{user?.role} Dashboard</p>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
        >
          Sign Out
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard title="Role" value={user?.role || '-'} />
        <DashboardCard title="Email" value={user?.email || '-'} />
        <DashboardCard title="Username" value={user?.username || '-'} />
        <DashboardCard title="Status" value={user?.is_active ? 'Active' : 'Inactive'} />
      </div>

      <div className="mt-8 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Quick Actions</h2>
        <p className="text-slate-500">
          Dashboard content will be role-specific. Your role:{' '}
          <strong className="capitalize">{user?.role}</strong>
        </p>
      </div>
    </div>
  );
}

function DashboardCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="text-lg font-semibold text-slate-800 mt-1 capitalize">{value}</p>
    </div>
  );
}
