import { useEffect, useState } from 'react';

/**
 * Shared async loader for simple API-backed pages.
 */
export function useApiResource<T>(
  fetchResource: () => Promise<T>,
  fallbackError = 'Failed to load data',
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const loadResource = async () => {
      setIsLoading(true);
      setError('');

      try {
        const response = await fetchResource();
        if (!isCancelled) {
          setData(response);
        }
      } catch (err) {
        if (!isCancelled) {
          const errorMessage = err instanceof Error ? err.message : fallbackError;
          setError(errorMessage);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    loadResource();

    return () => {
      isCancelled = true;
    };
  }, [fallbackError, fetchResource]);

  return { data, isLoading, error };
}
