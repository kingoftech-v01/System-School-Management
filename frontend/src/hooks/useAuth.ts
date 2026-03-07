import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/stores/auth';
import type { LoginRequest } from '@/types/api';

export function useAuth() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, user, setTokens, setUser, logout: clearAuth } = useAuthStore();

  // Fetch current user on mount if authenticated but no user loaded
  const { isLoading: isLoadingUser } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const me = await authApi.getMe();
      setUser(me);
      return me;
    },
    enabled: isAuthenticated && !user,
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      setUser(data.user);
      navigate('/dashboard');
    },
  });

  const logout = useCallback(async () => {
    const refresh = useAuthStore.getState().refreshToken;
    if (refresh) {
      await authApi.logout(refresh);
    }
    clearAuth();
    queryClient.clear();
    navigate('/login');
  }, [clearAuth, navigate, queryClient]);

  return {
    user,
    isAuthenticated,
    isLoadingUser,
    login: loginMutation.mutate,
    loginError: loginMutation.error,
    isLoggingIn: loginMutation.isPending,
    logout,
  };
}
