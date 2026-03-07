import { Tabs } from 'expo-router';
import { Text } from 'react-native';

export default function AppLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: '#0f172a' },
        headerTintColor: '#fff',
        tabBarActiveTintColor: '#2563eb',
        tabBarInactiveTintColor: '#94a3b8',
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Dashboard',
          headerTitle: 'Aurelius',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'📊'}</Text>,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'👤'}</Text>,
        }}
      />
    </Tabs>
  );
}
