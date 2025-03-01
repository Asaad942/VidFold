import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface AuthState {
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });

  useEffect(() => {
    loadToken();
  }, []);

  const loadToken = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      setAuthState({
        token,
        isLoading: false,
        isAuthenticated: !!token,
      });
    } catch (error) {
      console.error('Error loading token:', error);
      setAuthState({
        token: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
  };

  return authState;
}; 