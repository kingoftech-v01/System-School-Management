import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  ActivityIndicator, KeyboardAvoidingView, Platform
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { authApi } from '../../src/api/auth';
import { useAuthStore } from '../../src/stores/auth';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const setUser = useAuthStore((s) => s.setUser);

  const handleLogin = async () => {
    if (!username || !password) {
      setError('Please enter username and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const tokens = await authApi.login({ username, password });
      await SecureStore.setItemAsync('accessToken', tokens.access);
      await SecureStore.setItemAsync('refreshToken', tokens.refresh);
      setUser(tokens.user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1, backgroundColor: '#0f172a' }}
    >
      <View style={{ flex: 1, justifyContent: 'center', paddingHorizontal: 24 }}>
        <View style={{ alignItems: 'center', marginBottom: 40 }}>
          <Text style={{ fontSize: 36, fontWeight: 'bold', color: '#fff' }}>Aurelius</Text>
          <Text style={{ fontSize: 16, color: '#93c5fd', marginTop: 8 }}>
            School Management System
          </Text>
        </View>

        <View style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24 }}>
          <Text style={{ fontSize: 22, fontWeight: '600', color: '#1e293b', marginBottom: 20 }}>
            Sign In
          </Text>

          {error ? (
            <View style={{
              backgroundColor: '#fef2f2', borderWidth: 1, borderColor: '#fecaca',
              borderRadius: 8, padding: 12, marginBottom: 16
            }}>
              <Text style={{ color: '#dc2626', fontSize: 14 }}>{error}</Text>
            </View>
          ) : null}

          <Text style={{ fontSize: 14, fontWeight: '500', color: '#475569', marginBottom: 6 }}>
            Username
          </Text>
          <TextInput
            value={username}
            onChangeText={setUsername}
            placeholder="Enter your username"
            autoCapitalize="none"
            autoCorrect={false}
            style={{
              borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 8,
              paddingHorizontal: 16, paddingVertical: 12, fontSize: 16,
              marginBottom: 16, color: '#1e293b',
            }}
          />

          <Text style={{ fontSize: 14, fontWeight: '500', color: '#475569', marginBottom: 6 }}>
            Password
          </Text>
          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            style={{
              borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 8,
              paddingHorizontal: 16, paddingVertical: 12, fontSize: 16,
              marginBottom: 24, color: '#1e293b',
            }}
          />

          <TouchableOpacity
            onPress={handleLogin}
            disabled={loading}
            style={{
              backgroundColor: loading ? '#93c5fd' : '#2563eb',
              borderRadius: 8, paddingVertical: 14, alignItems: 'center',
            }}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={{ color: '#fff', fontSize: 16, fontWeight: '600' }}>Sign In</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
