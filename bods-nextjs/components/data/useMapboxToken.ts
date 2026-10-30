'use client';

import { useEffect, useState } from 'react';

/** The Mapbox public token, served at runtime by `app/api/mapbox-token`; '' until loaded. */
export function useMapboxToken(): string {
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

  return token;
}
