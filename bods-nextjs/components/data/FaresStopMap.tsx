/**
 * Fares dataset stop map: every stop point of the live revision as a teal dot,
 * with "Atco: <code>, Name: <name>" on hover, fitted to the stops.
 *
 * Source JS: transit_odp/frontend/assets/js/fares-detail-map.js (initFaresDetailMap)
 * Source markup: transit_odp/publish/templates/publish/snippets/dataset_map.html
 * API: /api/app/fare_stops/?revision={id} (data host)
 */

'use client';

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { dataApiPath } from '@/lib/api-paths';

export interface FaresStopMapProps {
  revisionId: number;
  mapboxToken: string;
}

interface StopFeature {
  geometry?: { coordinates?: unknown };
  properties?: { atco_code?: string; common_name?: string };
}

interface StopCollection {
  features: StopFeature[];
}

const SOURCE_ID = 'stop-points';

export function FaresStopMap({ revisionId, mapboxToken }: FaresStopMapProps) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;

    mapboxgl.accessToken = mapboxToken;
    const map = new mapboxgl.Map({
      container: container.current,
      style: 'mapbox://styles/mapbox/light-v9',
      center: [-1.1743, 52.3555],
      zoom: 5,
      maxZoom: 12,
    });
    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }));

    // Keep the map out of the tab order, like Django's script.
    map.getCanvas().setAttribute('tabindex', '-1');
    map
      .getContainer()
      .querySelectorAll('.mapboxgl-ctrl-logo, .mapboxgl-ctrl-zoom-in, .mapboxgl-ctrl-zoom-out')
      .forEach((element) => element.setAttribute('tabindex', '-1'));

    const popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });
    let cancelled = false;

    map.on('load', () => {
      fetch(`${dataApiPath('/api/app/fare_stops/')}?revision=${revisionId}`)
        .then((response) => (response.ok ? (response.json() as Promise<StopCollection>) : null))
        .then((geojson) => {
          if (cancelled || !geojson) return;

          map.addSource(SOURCE_ID, {
            type: 'geojson',
            data: geojson as unknown as GeoJSON.FeatureCollection,
          });
          map.addLayer({
            id: SOURCE_ID,
            type: 'circle',
            source: SOURCE_ID,
            paint: { 'circle-color': '#49A39A', 'circle-radius': 5 },
          });

          const bounds = new mapboxgl.LngLatBounds();
          geojson.features.forEach((feature) => {
            const coordinates = feature.geometry?.coordinates;
            if (Array.isArray(coordinates)) bounds.extend(coordinates as [number, number]);
          });
          if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 20 });
        })
        .catch(() => undefined);
    });

    map.on('mouseenter', SOURCE_ID, (event) => {
      map.getCanvas().style.cursor = 'pointer';
      const properties = event.features?.[0]?.properties;
      popup
        .setLngLat(event.lngLat)
        .setHTML(`Atco: ${properties?.atco_code}, Name: ${properties?.common_name}`)
        .addTo(map);
    });
    map.on('mouseleave', SOURCE_ID, () => {
      map.getCanvas().style.cursor = '';
      popup.remove();
    });

    return () => {
      cancelled = true;
      map.remove();
    };
  }, [revisionId, mapboxToken]);

  return <div ref={container} id="map" className="disruptions-width" />;
}
