import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { useAuthStore } from '../../src/stores/auth';

export default function ProfileScreen() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      <View style={{ padding: 24 }}>
        <View style={{ alignItems: 'center', marginBottom: 32 }}>
          <View style={{
            width: 80, height: 80, borderRadius: 40,
            backgroundColor: '#2563eb', alignItems: 'center',
            justifyContent: 'center', marginBottom: 12,
          }}>
            <Text style={{ fontSize: 32, color: '#fff', fontWeight: 'bold' }}>
              {user?.first_name?.[0] || 'U'}
            </Text>
          </View>
          <Text style={{ fontSize: 22, fontWeight: 'bold', color: '#1e293b' }}>
            {user?.first_name} {user?.last_name}
          </Text>
          <Text style={{ fontSize: 14, color: '#64748b', textTransform: 'capitalize' }}>
            {user?.role}
          </Text>
        </View>

        <View style={{
          backgroundColor: '#fff', borderRadius: 12,
          borderWidth: 1, borderColor: '#e2e8f0'
        }}>
          <ProfileRow label="Username" value={user?.username || '-'} />
          <ProfileRow label="Email" value={user?.email || '-'} />
          <ProfileRow label="Phone" value={user?.phone || '-'} />
          <ProfileRow label="Role" value={user?.role_display || user?.role || '-'} last />
        </View>

        <TouchableOpacity
          onPress={logout}
          style={{
            backgroundColor: '#ef4444', borderRadius: 12,
            paddingVertical: 14, alignItems: 'center', marginTop: 32,
          }}
        >
          <Text style={{ color: '#fff', fontSize: 16, fontWeight: '600' }}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

function ProfileRow({ label, value, last }: { label: string; value: string; last?: boolean }) {
  return (
    <View style={{
      flexDirection: 'row', justifyContent: 'space-between',
      paddingHorizontal: 16, paddingVertical: 14,
      borderBottomWidth: last ? 0 : 1, borderBottomColor: '#e2e8f0',
    }}>
      <Text style={{ fontSize: 14, color: '#64748b' }}>{label}</Text>
      <Text style={{ fontSize: 14, color: '#1e293b', fontWeight: '500' }}>{value}</Text>
    </View>
  );
}
