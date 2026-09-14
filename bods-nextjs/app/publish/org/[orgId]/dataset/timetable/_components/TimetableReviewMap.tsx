'use client';

import { useEffect, useState } from 'react';
import { RouteMap } from '@/components/data/RouteMap';

export function TimetableReviewMap({ revisionId }: { revisionId: number }) {
  const [token, setToken] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetch('/api/mapbox-token')
      .then((response) => response.json() as Promise<{ token?: string }>)
      .then((data) => {
        if (!cancelled) setToken(data.token || '');
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, []);

  if (!token) return null;

  return <RouteMap revisionId={revisionId} mapboxToken={token} ariaLabel="Interactive map showing timetable routes" />;
}