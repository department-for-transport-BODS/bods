'use client';

import dynamic from 'next/dynamic';
import { useMapboxToken } from './useMapboxToken';
import type { FaresStopMapProps } from './FaresStopMap';

const FaresStopMap = dynamic(() => import('./FaresStopMap').then((module) => module.FaresStopMap), {
  ssr: false,
});

export function MapboxFaresStopMap(props: Omit<FaresStopMapProps, 'mapboxToken'>) {
  const token = useMapboxToken();

  if (!token) return <div id="map" className="disruptions-width" />;

  return <FaresStopMap {...props} mapboxToken={token} />;
}
