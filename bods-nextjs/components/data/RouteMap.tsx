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
import { dataApiPath } from '@/lib/api-paths';
import styles from './RouteMap.module.css';

export interface RouteMapProps {
  revisionId?: number;
  apiRoot?: string;
  mapboxToken: string;
  lineName?: string;
  serviceCodes?: string;
  /** Licence pages: show every service pattern on one licence (API `licence_number`). */
  licenceNumber?: string;
  /** Licence pages: comma separated "<service> - <registration>" values (API `registration_number`). */
  registrationNumbers?: string;
  /** When set, plots live vehicles from this URL every 10 seconds (Django `fetchAvlLiveLocation`). */
  liveLocationUrl?: string;
  /** Called with Django's "Last updated at - <time>" text on each live poll. */
  onLiveUpdate?: (text: string) => void;
  ariaLabel?: string;
  showTimestamp?: boolean;
  containerClassName?: string;
}

interface LiveVehicle {
  Longitude: number;
  Latitude: number;
  VehicleJourneyCode?: string;
}

const LIVE_POLL_INTERVAL_MS = 10000;

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}

// Django's getCurrentDateTime(): dd/mm/yyyy hh:mm:ss AM|PM.
function liveTimestamp(now: Date): string {
  const pad = (value: number) => String(value).padStart(2, '0');
  const hours = now.getHours();
  return `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(hours % 12 || 12)}:${pad(
    now.getMinutes(),
  )}:${pad(now.getSeconds())} ${hours >= 12 ? 'PM' : 'AM'}`;
}

const VEHICLE_ICON =
  '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" x="0px" y="0px" viewBox="0 0 100 125" xml:space="preserve"><style type="text/css">.st0{fill-rule:evenodd;clip-rule:evenodd;}</style><path class="st0" d="M64.2,78.4h14.2v4.7c0,2.6-2.1,4.7-4.7,4.7h-4.7c-2.6,0-4.7-2.1-4.7-4.7V78.4z"/><path class="st0" d="M21.6,78.4h14.2v4.7c0,2.6-2.1,4.7-4.7,4.7h-4.7c-2.6,0-4.7-2.1-4.7-4.7V78.4z"/><path class="st0" d="M87,27h1.6c2.4,0,4.4,1.7,4.4,3.8v4.5c0,2.1-2,3.8-4.4,3.8H87V27z"/><path class="st0" d="M75.4,12.2H24.6c-5.2,0-9.5,4.2-9.5,9.5V67c0,5.2,4.2,9.5,9.5,9.5h50.7c5.2,0,9.5-4.2,9.5-9.5V21.6  C84.8,16.4,80.6,12.2,75.4,12.2z M28.7,68.9c-3.2,0-5.8-2.5-5.8-5.7c0-3.1,2.6-5.7,5.8-5.7s5.8,2.5,5.8,5.7  C34.5,66.4,31.9,68.9,28.7,68.9z M71.3,68.9c-3.2,0-5.8-2.5-5.8-5.7c0-3.1,2.6-5.7,5.8-5.7s5.8,2.5,5.8,5.7  C77.1,66.4,74.5,68.9,71.3,68.9z M78.4,43.3c0,2.6-2.1,4.7-4.7,4.7H26.4c-2.6,0-4.7-2.1-4.7-4.7V24.4c0-2.6,2.1-4.7,4.7-4.7h47.3  c2.6,0,4.7,2.1,4.7,4.7V43.3z"/><path class="st0" d="M12.9,27h-1.6c-2.4,0-4.4,1.7-4.4,3.8v4.5c0,2.1,2,3.8,4.4,3.8h1.6V27z"/></svg>';

function createVehicleElement(): HTMLDivElement {
  const element = document.createElement('div');
  element.innerHTML = VEHICLE_ICON;
  element.style.width = '30px';
  element.style.height = '30px';
  element.style.backgroundSize = 'cover';
  return element;
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
  apiRoot,
  mapboxToken,
  lineName,
  serviceCodes,
  licenceNumber,
  registrationNumbers,
  liveLocationUrl,
  onLiveUpdate,
  ariaLabel = 'Interactive map showing bus route lines',
  showTimestamp = false,
  containerClassName,
}: RouteMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const popup = useRef<mapboxgl.Popup | null>(null);
  const fetchAndDisplayRoutesRef = useRef<() => void>(() => undefined);
  const mapLoaded = useRef(false);
  const liveMarkers = useRef<Record<string, mapboxgl.Marker>>({});
  const onLiveUpdateRef = useRef(onLiveUpdate);
  const [mapReady, setMapReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const hoveredStateId = useRef<number | null>(null);

  onLiveUpdateRef.current = onLiveUpdate;

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
      mapLoaded.current = true;
      setMapReady(true);
      fetchAndDisplayRoutesRef.current();
    });

    return () => {
      mapLoaded.current = false;
      setMapReady(false);
      liveMarkers.current = {};
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [revisionId, mapboxToken, ariaLabel]);

  // The licence page re-plots the map whenever its service filters change.
  const previousRegistrationNumbers = useRef(registrationNumbers);
  useEffect(() => {
    if (previousRegistrationNumbers.current === registrationNumbers) return;
    previousRegistrationNumbers.current = registrationNumbers;
    if (mapLoaded.current) fetchAndDisplayRoutesRef.current();
  }, [registrationNumbers]);

  useEffect(() => {
    if (!liveLocationUrl || !mapReady) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const poll = () => {
      fetch(liveLocationUrl)
        .then((response) => response.json() as Promise<Record<string, LiveVehicle>>)
        .then((vehicles) => {
          if (cancelled || !map.current) return;
          const markers = liveMarkers.current;
          Object.entries(vehicles).forEach(([vehicleRef, vehicle]) => {
            const lngLat: [number, number] = [vehicle.Longitude, vehicle.Latitude];
            if (markers[vehicleRef]) {
              markers[vehicleRef].setLngLat(lngLat);
              return;
            }
            markers[vehicleRef] = new mapboxgl.Marker(createVehicleElement())
              .setLngLat(lngLat)
              .setPopup(
                new mapboxgl.Popup().setHTML(
                  `<h3>Vehicle Ref: ${escapeHtml(vehicleRef)}</h3><p>Vehicle Journey Code: ${escapeHtml(
                    String(vehicle.VehicleJourneyCode ?? ''),
                  )}</p>`,
                ),
              )
              .addTo(map.current!);
          });
          Object.keys(markers).forEach((vehicleRef) => {
            if (!(vehicleRef in vehicles)) {
              markers[vehicleRef].remove();
              delete markers[vehicleRef];
            }
          });
        })
        .catch((err: unknown) => console.log(`Error while calling AVL real time data API${String(err)}`));
      onLiveUpdateRef.current?.(`Last updated at - ${liveTimestamp(new Date())}`);
      timer = setTimeout(poll, LIVE_POLL_INTERVAL_MS);
    };
    poll();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [liveLocationUrl, mapReady]);

  const buildApiUrl = (): string => {
    const params = new URLSearchParams();
    if (revisionId) params.append('revision', revisionId.toString());
    if (lineName) params.append('line_name', lineName);
    if (serviceCodes) params.append('service_codes', serviceCodes);
    if (licenceNumber) params.append('licence_number', licenceNumber);
    if (registrationNumbers) params.append('registration_number', registrationNumbers);
    const path = '/api/app/service_pattern/';
    const endpoint = apiRoot ? `${apiRoot}${path}` : dataApiPath(path);
    return `${endpoint}?${params.toString()}`;
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

  fetchAndDisplayRoutesRef.current = fetchAndDisplayRoutes;

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
    <div className={containerClassName ?? styles.routeMapContainer}>
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
