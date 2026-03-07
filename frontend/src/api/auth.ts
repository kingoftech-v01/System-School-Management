import axios from 'axios';
import apiClient from './client';
import type { AuthTokens, LoginRequest, User, NavigationResponse, PermissionsResponse } from '@/types/api';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthTokens> => {
    const response = await axios.post('/api/v1/accounts/auth/login/', credentials);
    return response.data;
  },

  logout: async (refresh: string) => {
    try {
      await apiClient.post('/accounts/auth/logout/', { refresh });
    } catch {
      // Ignore errors on logout
    }
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/accounts/users/me/');
    return response.data;
  },

  getNavigation: async (): Promise<NavigationResponse> => {
    const response = await apiClient.get('/accounts/navigation/');
    return response.data;
  },

  getPermissions: async (): Promise<PermissionsResponse> => {
    const response = await apiClient.get('/accounts/permissions/');
    return response.data;
  },

  changePassword: async (data: { old_password: string; new_password: string; new_password_confirm: string }) => {
    return apiClient.post('/accounts/users/change_password/', data);
  },
};
