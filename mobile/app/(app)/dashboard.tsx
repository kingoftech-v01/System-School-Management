import { View, Text, ScrollView } from 'react-native';
import { useAuthStore } from '../../src/stores/auth';

export default function DashboardScreen() {
  const user = useAuthStore((s) => s.user);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      <View style={{ padding: 24 }}>
        <Text style={{ fontSize: 28, fontWeight: 'bold', color: '#1e293b' }}>
          Welcome, {user?.first_name || 'User'}
        </Text>
        <Text style={{ fontSize: 16, color: '#64748b', marginTop: 4, textTransform: 'capitalize' }}>
          {user?.role} Dashboard
        </Text>

        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 16, marginTop: 24 }}>
          <DashboardCard title="Role" value={user?.role || '-'} />
          <DashboardCard title="Email" value={user?.email || '-'} />
          <DashboardCard title="Username" value={user?.username || '-'} />
          <DashboardCard title="Status" value="Active" />
        </View>
      </View>
    </ScrollView>
  );
}

function DashboardCard({ title, value }: { title: string; value: string }) {
  return (
    <View style={{
      backgroundColor: '#fff', borderRadius: 12, padding: 16,
      borderWidth: 1, borderColor: '#e2e8f0', minWidth: '45%', flex: 1,
    }}>
      <Text style={{ fontSize: 13, color: '#64748b' }}>{title}</Text>
      <Text style={{
        fontSize: 16, fontWeight: '600', color: '#1e293b',
        marginTop: 4, textTransform: 'capitalize'
      }}>
        {value}
      </Text>
    </View>
  );
}
