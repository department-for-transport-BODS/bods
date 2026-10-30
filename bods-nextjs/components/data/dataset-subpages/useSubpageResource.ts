import { notFound } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ApiError, api } from '@/lib/api-client';

type Outcome<T> = { path: string; data: T } | { path: string; error: string } | { path: string; missing: true };

interface SubpageResource<T> {
  data: T | null;
  error: string | null;
}

/**
 * Loads a dataset sub-page payload. A 404 from Django (unknown dataset, wrong
 * dataset type, page out of range) renders Next's not-found page, like the
 * Django views' Http404.
 */
export function useSubpageResource<T>(path: string, fallbackError: string): SubpageResource<T> {
  const [outcome, setOutcome] = useState<Outcome<T> | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .get<T>(path)
      .then((data) => {
        if (!cancelled) setOutcome({ path, data });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 404) {
          setOutcome({ path, missing: true });
          return;
        }
        setOutcome({ path, error: fallbackError });
      });

    return () => {
      cancelled = true;
    };
  }, [path, fallbackError]);

  // An outcome for a previous path is stale: show nothing until the new one lands.
  const current = outcome?.path === path ? outcome : null;
  if (current && 'missing' in current) notFound();

  return {
    data: current && 'data' in current ? current.data : null,
    error: current && 'error' in current ? current.error : null,
  };
}
