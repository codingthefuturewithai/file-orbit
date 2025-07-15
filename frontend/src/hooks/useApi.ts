import { useState, useCallback } from 'react';
import { notifications } from '@mantine/notifications';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const callApi = useCallback(async <T = any>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    data?: any
  ): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);

      const url = `${API_BASE_URL}/api/v1${endpoint}`;
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err: any) {
      setError(err);
      console.error('API Error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { callApi, loading, error };
}