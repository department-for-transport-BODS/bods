'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api-client';

type ReviewStatus = {
  loading: boolean;
  progress: number;
};

type ProgressResponse = {
  progress: number;
  status: string;
};

export type DatasetReviewOptions<T> = {
  // Render straight from the review status when processing has already finished.
  fetchReviewFirst?: boolean;
  // Keep re-fetching the review status after processing, e.g. while a DQ report is pending.
  keepPollingReview?: (data: T) => boolean;
};

const POLL_INTERVAL_MS = 1000;
export const REVIEW_POLL_INTERVAL_MS = 10000;
const PENDING_STATUS = 'pending';

export function useDatasetReview<T extends ReviewStatus>(
  datasetId: string,
  reviewPath: string,
  requestErrorMessage?: string,
  refreshKey = '',
  options: DatasetReviewOptions<T> = {},
) {
  const { fetchReviewFirst = false } = options;
  const keepPollingReviewRef = useRef(options.keepPollingReview);
  keepPollingReviewRef.current = options.keepPollingReview;

  const [statusData, setStatusData] = useState<T | null>(null);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isCancelled = false;
    let isFetchingProgress = false;
    let progressIntervalId: ReturnType<typeof setInterval> | undefined;
    let reviewIntervalId: ReturnType<typeof setInterval> | undefined;

    const setRequestError = (error: unknown) => {
      if (isCancelled) return;
      setErrorMessage(
        requestErrorMessage ?? (error instanceof Error
          ? error.message
          : 'Unable to check processing status. Please refresh and try again.'),
      );
      setIsInitialLoading(false);
    };

    const fetchReview = async (): Promise<T | null> => {
      const data = await api.get<T>(reviewPath);
      if (isCancelled) return null;
      setStatusData(data);
      setErrorMessage('');
      setIsInitialLoading(false);
      return data;
    };

    const stopProgressPolling = () => {
      clearInterval(progressIntervalId);
      progressIntervalId = undefined;
    };

    const stopReviewPolling = () => {
      clearInterval(reviewIntervalId);
      reviewIntervalId = undefined;
    };

    const pollReview = async () => {
      try {
        const data = await fetchReview();
        if (data && !keepPollingReviewRef.current?.(data)) {
          stopReviewPolling();
        }
      } catch {
        // Matches legacy dqs-review-panel.js, which ignores failed status checks and retries.
      }
    };

    const handleProcessingComplete = (data: T) => {
      stopProgressPolling();
      if (keepPollingReviewRef.current?.(data)) {
        reviewIntervalId ??= setInterval(pollReview, REVIEW_POLL_INTERVAL_MS);
      } else {
        stopReviewPolling();
      }
    };

    const fetchProgress = async () => {
      if (isFetchingProgress) return;
      isFetchingProgress = true;
      try {
        const data = await api.get<ProgressResponse>(
          `/api/publish/dataset/${datasetId}/progress/`,
        );

        if (isCancelled) return;
        setProcessingProgress(data.progress);
        setErrorMessage('');
        setIsInitialLoading(false);

        if (data.progress === 100 && data.status !== PENDING_STATUS) {
          const review = await fetchReview();
          // Progress can reach 100 before the revision leaves a loading status, so keep polling.
          if (review && !review.loading) {
            handleProcessingComplete(review);
          }
        }
      } catch (error) {
        setRequestError(error);
      } finally {
        isFetchingProgress = false;
      }
    };

    const startProgressPolling = () => {
      progressIntervalId ??= setInterval(fetchProgress, POLL_INTERVAL_MS);
      fetchProgress();
    };

    const start = async () => {
      if (fetchReviewFirst) {
        try {
          const review = await fetchReview();
          if (!review) return;
          if (!review.loading) {
            handleProcessingComplete(review);
            return;
          }
          setProcessingProgress(review.progress);
        } catch (error) {
          setRequestError(error);
        }
      }
      if (!isCancelled) startProgressPolling();
    };

    start();
    window.addEventListener('pageshow', fetchProgress);
    window.addEventListener('focus', fetchProgress);

    return () => {
      isCancelled = true;
      stopProgressPolling();
      stopReviewPolling();
      window.removeEventListener('pageshow', fetchProgress);
      window.removeEventListener('focus', fetchProgress);
    };
  }, [datasetId, fetchReviewFirst, refreshKey, requestErrorMessage, reviewPath]);

  return {
    statusData,
    processingProgress,
    isInitialLoading,
    errorMessage,
    setErrorMessage,
  };
}