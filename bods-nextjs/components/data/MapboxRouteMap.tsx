'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import type { RouteMapProps } from './RouteMap';

const RouteMap = dynamic(() => import('./RouteMap').then((module) => module.RouteMap), { ssr: false });

export function MapboxRouteMap(props: Omit<RouteMapProps, 'mapboxToken'>) {
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

  if (!token) return <div className="disruptions-width" />;

  return <RouteMap {...props} mapboxToken={token} />;
}
