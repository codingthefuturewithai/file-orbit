import { useState, useCallback } from 'react';
import { notifications } from '@mantine/notifications';

interface UseApiOptions {
  showSuccessNotification?: boolean;
  successMessage?: string;
  errorMessage?: string;
}

export const useApi = <T = any>(
  apiCall: () => Promise<T>,
  options: UseApiOptions = {}
) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
      
      if (options.showSuccessNotification && options.successMessage) {
        notifications.show({
          title: 'Success',
          message: options.successMessage,
          color: 'green',
        });
      }
      
      return result;
    } catch (err: any) {
      const error = err as Error;
      setError(error);
      
      notifications.show({
        title: 'Error',
        message: options.errorMessage || err.response?.data?.detail || err.message || 'An error occurred',
        color: 'red',
      });
      
      throw error;
    } finally {
      setLoading(false);
    }
  }, [apiCall, options]);

  return { execute, loading, error, data };
};