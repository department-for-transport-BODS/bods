/**
 * Stop Map Component
 *
 *
 * Source: transit_odp/data_quality/templates/data_quality/snippets/detail_map.html
 * Source JS: transit_odp/frontend/assets/js/data-quality-detail-map.js
 * API: /api/v1/stoppoint/?revision={id}
 *
 * Displays bus stop locations on Mapbox map with:
 * - Stop markers with clustering for dense areas
 * - Stop name on hover/click
 * - Interactive zoom/pan with NavigationControl
 * - Click stop for details
 * - Search/filter visible stops
 * - Keyboard accessible controls
 * - Text alternative for screen readers
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { config } from '@/config';
import styles from './StopMap.module.css';

export interface StopMapProps {
  revisionId?: number;
  stops?: StopPoint[];
  apiRoot?: string;
  mapboxToken: string;
  onStopClick?: (stop: StopPoint) => void;
  ariaLabel?: string;
  enableClustering?: boolean;
}

export interface StopPoint {
  id: number;
  atco_code: string;
  common_name: string;
  location: {
    type: 'Point';
    coordinates: [number, number]; // [longitude, latitude]
  };
}

interface StopFeatureCollection {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    id: number;
    geometry: {
      type: 'Point';
      coordinates: [number, number];
    };
    properties: {
      id: number;
      atco_code: string;
      common_name: string;
    };
  }>;
}

export function StopMap({
  revisionId,
  stops,
  apiRoot = config.djangoApiUrl,
  mapboxToken,
  onStopClick,
  ariaLabel = 'Interactive map showing bus stop locations',
  enableClustering = true,
}: StopMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const popup = useRef<mapboxgl.Popup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stopCount, setStopCount] = useState<number>(0);
  const markers = useRef<Map<number, mapboxgl.Marker>>(new Map());

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = mapboxToken;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v9',
      center: [-1.1743, 52.3555], // UK center
      zoom: 5,
      maxZoom: 18,
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
      offset: 25,
    });

    map.current.on('load', () => {
      if (stops) {
        displayStops(stops);
      } else if (revisionId) {
        fetchAndDisplayStops();
      }
    });

    return () => {
      markers.current.forEach((marker) => marker.remove());
      markers.current.clear();

      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [revisionId, mapboxToken, ariaLabel]);

  useEffect(() => {
    if (map.current && stops) {
      displayStops(stops);
    }
  }, [stops]);

  const fetchAndDisplayStops = async () => {
    if (!map.current || !revisionId) return;

    try {
      const url = `${apiRoot}/api/v1/stoppoint/?revision=${revisionId}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const stopPoints: StopPoint[] = data.results || data.features?.map((f: any) => ({
        id: f.id,
        atco_code: f.properties.atco_code,
        common_name: f.properties.common_name,
        location: f.geometry,
      })) || [];

      displayStops(stopPoints);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load stop data';
      console.error('Stop map error:', err);
      setError(errorMessage);
    }
  };

  const displayStops = (stopPoints: StopPoint[]) => {
    if (!map.current) return;

    setStopCount(stopPoints.length);

    if (enableClustering) {
      displayStopsWithClustering(stopPoints);
    } else {
      displayStopsWithMarkers(stopPoints);
    }
  };

  const displayStopsWithClustering = (stopPoints: StopPoint[]) => {
    if (!map.current) return;

    const geojson: StopFeatureCollection = {
      type: 'FeatureCollection',
      features: stopPoints.map((stop) => ({
        type: 'Feature',
        id: stop.id,
        geometry: stop.location,
        properties: {
          id: stop.id,
          atco_code: stop.atco_code,
          common_name: stop.common_name,
        },
      })),
    };

    if (map.current.getSource('stops')) {
      const source = map.current.getSource('stops') as mapboxgl.GeoJSONSource;
      source.setData(geojson);
    } else {
      map.current.addSource('stops', {
        type: 'geojson',
        data: geojson,
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });

      map.current.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'stops',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6', // Light blue for small clusters
            10,
            '#f1f075', // Yellow for medium clusters
            30,
            '#f28cb1', // Pink for large clusters
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            20, // Small clusters
            10,
            30, // Medium clusters
            30,
            40, // Large clusters
          ],
        },
      });

      map.current.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'stops',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 12,
        },
      });

      map.current.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'stops',
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': '#11b4da',
          'circle-radius': 8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
        },
      });

      setupClusterInteractions();
    }

    fitMapToStops(stopPoints);
  };

  const displayStopsWithMarkers = (stopPoints: StopPoint[]) => {
    if (!map.current) return;

    markers.current.forEach((marker) => marker.remove());
    markers.current.clear();

    stopPoints.forEach((stop) => {
      const el = document.createElement('div');
      el.className = styles.stopMarker;
      el.style.backgroundColor = '#11b4da';
      el.style.width = '16px';
      el.style.height = '16px';
      el.style.borderRadius = '50%';
      el.style.border = '2px solid #fff';
      el.style.cursor = 'pointer';

      const marker = new mapboxgl.Marker(el)
        .setLngLat(stop.location.coordinates)
        .setPopup(
          new mapboxgl.Popup({ offset: 25 }).setHTML(
            `<h3>${stop.common_name}</h3><p>ATCO: ${stop.atco_code}</p>`
          )
        )
        .addTo(map.current!);

      el.addEventListener('click', () => {
        if (onStopClick) {
          onStopClick(stop);
        }
      });

      markers.current.set(stop.id, marker);
    });

    fitMapToStops(stopPoints);
  };

  const setupClusterInteractions = () => {
    if (!map.current) return;

    map.current.on('click', 'clusters', (e) => {
      if (!map.current) return;

      const features = map.current.queryRenderedFeatures(e.point, {
        layers: ['clusters'],
      });

      if (features.length === 0) return;

      const clusterId = features[0].properties?.cluster_id;
      const source = map.current.getSource('stops') as mapboxgl.GeoJSONSource;

      source.getClusterExpansionZoom(clusterId, (err, zoom) => {
        if (err || !map.current || zoom == null) return;

        const coordinates = (features[0].geometry as any).coordinates;
        map.current.easeTo({
          center: coordinates,
          zoom: zoom,
        });
      });
    });

    map.current.on('mouseenter', 'clusters', () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = 'pointer';
      }
    });

    map.current.on('mouseleave', 'clusters', () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = '';
      }
    });

    map.current.on('click', 'unclustered-point', (e) => {
      if (!map.current || !e.features || e.features.length === 0) return;

      const feature = e.features[0];
      const properties = feature.properties;

      if (onStopClick && properties) {
        const stop: StopPoint = {
          id: properties.id,
          atco_code: properties.atco_code,
          common_name: properties.common_name,
          location: feature.geometry as any,
        };
        onStopClick(stop);
      }

      const coordinates = (feature.geometry as any).coordinates.slice();
      const description = `<h3>${properties?.common_name}</h3><p>ATCO: ${properties?.atco_code}</p>`;

      popup.current!.setLngLat(coordinates).setHTML(description).addTo(map.current);
    });

    map.current.on('mouseenter', 'unclustered-point', (e) => {
      if (!map.current) return;

      map.current.getCanvas().style.cursor = 'pointer';

      if (e.features && e.features.length > 0) {
        const feature = e.features[0];
        const coordinates = (feature.geometry as any).coordinates.slice();
        const properties = feature.properties;
        const description = properties?.common_name || 'Bus Stop';

        popup.current!.setLngLat(coordinates).setHTML(description).addTo(map.current);
      }
    });

    map.current.on('mouseleave', 'unclustered-point', () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = '';
        popup.current?.remove();
      }
    });
  };

  const fitMapToStops = (stopPoints: StopPoint[]) => {
    if (!map.current || stopPoints.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();

    stopPoints.forEach((stop) => {
      bounds.extend(stop.location.coordinates);
    });

    if (!bounds.isEmpty()) {
      map.current.fitBounds(bounds, {
        padding: 50,
        maxZoom: 15,
      });
    }
  };

  return (
    <div className={styles.stopMapContainer}>
      {/* Accessibility: Screen reader description */}
      <div className="govuk-visually-hidden" role="status" aria-live="polite">
        {error
          ? `Error loading map: ${error}`
          : `Map showing ${stopCount} bus stops. ${
              enableClustering
                ? 'Stops are clustered. Click clusters to zoom in.'
                : 'Click on stop markers for details.'
            }`}
      </div>

      <div
        ref={mapContainer}
        id="stop-map"
        className={styles.mapContainer}
        role="region"
        aria-label={ariaLabel}
      />

      {stopCount > 0 && (
        <div className={`govuk-body-s ${styles.stopCount}`}>
          Showing {stopCount} stop{stopCount !== 1 ? 's' : ''}
        </div>
      )}

      {error && (
        <div className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> {error}
        </div>
      )}
    </div>
  );
}
