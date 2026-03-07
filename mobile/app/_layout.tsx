import { useEffect } from 'react';
import { Slot, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as SecureStore from 'expo-secure-store';
import { useAuthStore } from '../src/stores/auth';
import { authApi } from '../src/api/auth';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function AuthGate() {
  const router = useRouter();
  const segments = useSegments();
  const { isAuthenticated, isLoading, setUser, setAuthenticated, setLoading } = useAuthStore();

  useEffect(() => {
    async function checkAuth() {
      try {
        const token = await SecureStore.getItemAsync('accessToken');
        if (token) {
          const user = await authApi.getMe();
          setUser(user);
        }
      } catch {
        await SecureStore.deleteItemAsync('accessToken');
        await SecureStore.deleteItemAsync('refreshToken');
        setAuthenticated(false);
      } finally {
        setLoading(false);
      }
    }
    checkAuth();
  }, []);

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';
    if (!isAuthenticated && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      router.replace('/(app)/dashboard');
    }
  }, [isAuthenticated, segments, isLoading]);

  return <Slot />;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="auto" />
      <AuthGate />
    </QueryClientProvider>
  );
}
