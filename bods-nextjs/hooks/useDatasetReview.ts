'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api-client';

type ReviewStatus = {
  loading: boolean;
  progress: number;
};

type ProgressResponse = {
  progress: number;
  status: string;
};

const POLL_INTERVAL_MS = 1000;
const PENDING_STATUS = 'pending';

export function useDatasetReview<T extends ReviewStatus>(
  datasetId: string,
  reviewPath: string,
  requestErrorMessage?: string,
  refreshKey = '',
) {
  const [statusData, setStatusData] = useState<T | null>(null);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const fetchReview = async () => {
      const data = await api.get<T>(reviewPath);
      if (!isCancelled) {
        setStatusData(data);
        setErrorMessage('');
        setIsInitialLoading(false);
      }
    };

    const fetchProgress = async () => {
      try {
        const data = await api.get<ProgressResponse>(
          `/api/publish/dataset/${datasetId}/progress/`,
        );

        if (!isCancelled) {
          setProcessingProgress(data.progress);
          setErrorMessage('');
          setIsInitialLoading(false);
        }

        if (data.progress === 100 && data.status !== PENDING_STATUS) {
          clearInterval(intervalId);
          await fetchReview();
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(
            requestErrorMessage ?? (error instanceof Error
              ? error.message
              : 'Unable to check processing status. Please refresh and try again.'),
          );
          setIsInitialLoading(false);
        }
      }
    };

    const intervalId = setInterval(fetchProgress, POLL_INTERVAL_MS);
    fetchProgress();
    window.addEventListener('pageshow', fetchProgress);
    window.addEventListener('focus', fetchProgress);

    return () => {
      isCancelled = true;
      clearInterval(intervalId);
      window.removeEventListener('pageshow', fetchProgress);
      window.removeEventListener('focus', fetchProgress);
    };
  }, [datasetId, refreshKey, requestErrorMessage, reviewPath]);

  return {
    statusData,
    processingProgress,
    isInitialLoading,
    errorMessage,
    setErrorMessage,
  };
}