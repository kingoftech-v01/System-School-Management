import axios from 'axios';
import apiClient from './client';
import type { AuthTokens, LoginRequest, User } from '../types/api';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:9000/api/v1';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthTokens> => {
    const response = await axios.post(`${API_BASE_URL}/accounts/auth/login/`, credentials);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/accounts/users/me/');
    return response.data;
  },

  logout: async (refresh: string) => {
    try {
      await apiClient.post('/accounts/auth/logout/', { refresh });
    } catch {
      // Ignore errors on logout
    }
  },
};
