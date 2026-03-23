/**
 * Route Map Component
 * Displays bus routes on Mapbox map with:
 * - Route lines with hover effects
 * - Interactive zoom/pan with NavigationControl
 *
*/

'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { config } from '@/config';
import styles from './RouteMap.module.css';

export interface RouteMapProps {
  revisionId: number;
  apiRoot?: string;
  mapboxToken: string;
  lineName?: string;
  serviceCodes?: string;
  ariaLabel?: string;
  showTimestamp?: boolean;
}

interface ServicePatternFeature {
  type: 'Feature';
  id: number;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  };
  properties: {
    line_name: string;
    service_name?: string;
    origin?: string;
    destination?: string;
  };
}

interface ServicePatternCollection {
  type: 'FeatureCollection';
  features: ServicePatternFeature[];
}

export function RouteMap({
  revisionId,
  apiRoot = config.djangoApiUrl,
  mapboxToken,
  lineName,
  serviceCodes,
  ariaLabel = 'Interactive map showing bus route lines',
  showTimestamp = false,
}: RouteMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const popup = useRef<mapboxgl.Popup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const hoveredStateId = useRef<number | null>(null);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = mapboxToken;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v9',
      center: [-1.1743, 52.3555], // UK center
      zoom: 5,
      maxZoom: 12,
    });

    map.current.addControl(
      new mapboxgl.NavigationControl({ showCompass: false })
    );

    const canvas = map.current.getCanvas();
    canvas.setAttribute('tabindex', '-1');
    canvas.setAttribute('aria-label', ariaLabel);

    const container = map.current.getContainer();
    const logoElements = container.querySelectorAll('.mapboxgl-ctrl-logo');
    logoElements.forEach((el) => el.setAttribute('tabindex', '-1'));

    const controlButtons = container.querySelectorAll('button');
    controlButtons.forEach((btn) => btn.setAttribute('tabindex', '-1'));

    popup.current = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    map.current.on('load', () => {
      fetchAndDisplayRoutes();
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [revisionId, mapboxToken, ariaLabel]);

  const buildApiUrl = (): string => {
    const params = new URLSearchParams();
    if (revisionId) params.append('revision', revisionId.toString());
    if (lineName) params.append('line_name', lineName);
    if (serviceCodes) params.append('service_codes', serviceCodes);
    return `${apiRoot}/api/v1/service_pattern/?${params.toString()}`;
  };

  const fetchAndDisplayRoutes = async () => {
    if (!map.current) return;

    try {
      const url = buildApiUrl();
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const geojson: ServicePatternCollection = await response.json();

      if (map.current.getSource('service-patterns')) {
        const source = map.current.getSource('service-patterns') as mapboxgl.GeoJSONSource;
        source.setData(geojson);
      } else {
        map.current.addSource('service-patterns', {
          type: 'geojson',
          data: geojson,
        });

        map.current.addLayer({
          id: 'service-patterns',
          type: 'line',
          source: 'service-patterns',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#49A39A', // Teal color from Django
            'line-width': 2,
          },
        });

        map.current.addLayer({
          id: 'service-patterns-hover',
          type: 'line',
          source: 'service-patterns',
          layout: {},
          paint: {
            'line-color': '#34746e', // Darker teal on hover
            'line-width': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              4.5,
              0,
            ],
          },
        });

        setupHoverInteractions();
      }

      fitMapToRoutes(geojson);

      if (showTimestamp) {
        const now = new Date();
        setLastUpdated(now.toLocaleString('en-GB', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        }));
      }

      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load route data';
      console.error('Route map error:', err);
      setError(errorMessage);
    }
  };

  const setupHoverInteractions = () => {
    if (!map.current || !popup.current) return;

    map.current.on('mousemove', 'service-patterns', (e) => {
      if (!map.current || e.features?.length === 0) return;

      map.current.getCanvas().style.cursor = 'pointer';

      if (hoveredStateId.current !== null) {
        map.current.setFeatureState(
          { source: 'service-patterns', id: hoveredStateId.current },
          { hover: false }
        );
      }

      const feature = e.features![0];
      hoveredStateId.current = feature.id as number;

      map.current.setFeatureState(
        { source: 'service-patterns', id: hoveredStateId.current },
        { hover: true }
      );

      const properties = feature.properties;
      const description = `Service number: ${properties?.line_name || 'Unknown'}`;

      popup.current!
        .setLngLat(e.lngLat)
        .setHTML(description)
        .addTo(map.current);
    });

    map.current.on('mouseleave', 'service-patterns', () => {
      if (!map.current) return;

      map.current.getCanvas().style.cursor = '';

      if (hoveredStateId.current !== null) {
        map.current.setFeatureState(
          { source: 'service-patterns', id: hoveredStateId.current },
          { hover: false }
        );
        hoveredStateId.current = null;
      }

      popup.current?.remove();
    });
  };

  const fitMapToRoutes = (geojson: ServicePatternCollection) => {
    if (!map.current || geojson.features.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();

    geojson.features.forEach((feature) => {
      if (feature.geometry?.coordinates) {
        feature.geometry.coordinates.forEach((coord) => {
          bounds.extend(coord as [number, number]);
        });
      }
    });

    if (!bounds.isEmpty()) {
      map.current.fitBounds(bounds, {
        padding: 20,
      });
    }
  };

  return (
    <div className={styles.routeMapContainer}>
      {/* Accessibility: Screen reader description */}
      <div className="govuk-visually-hidden" role="status" aria-live="polite">
        {error
          ? `Error loading map: ${error}`
          : 'Map showing bus routes. Use zoom controls to navigate.'}
      </div>

      {/* Map container matching Django template */}
      <div
        ref={mapContainer}
        id="map"
        className={styles.mapContainer}
        role="region"
        aria-label={ariaLabel}
      />

      {showTimestamp && lastUpdated && (
        <span className={`govuk-body-s ${styles.updatedTimestamp}`}>
          Last updated at - {lastUpdated}
        </span>
      )}

      {error && (
        <div className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> {error}
        </div>
      )}
    </div>
  );
}
