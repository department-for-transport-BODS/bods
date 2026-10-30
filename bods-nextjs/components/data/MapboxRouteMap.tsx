'use client';

import dynamic from 'next/dynamic';
import type { RouteMapProps } from './RouteMap';
import { useMapboxToken } from './useMapboxToken';

const RouteMap = dynamic(() => import('./RouteMap').then((module) => module.RouteMap), { ssr: false });

export function MapboxRouteMap(props: Omit<RouteMapProps, 'mapboxToken'>) {
  const token = useMapboxToken();

  if (!token) return <div className="disruptions-width" />;

  return <RouteMap {...props} mapboxToken={token} />;
}
