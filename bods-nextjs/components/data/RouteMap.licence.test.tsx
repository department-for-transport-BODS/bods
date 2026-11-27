/**
 * RouteMap - licence page additions: licence/registration filters, refetch on filter change,
 * and live vehicle markers (feed-detail-map.js behaviour).
 */

import { act, render, waitFor } from '@testing-library/react';
import mapboxgl from 'mapbox-gl';
import { RouteMap } from './RouteMap';

const mockMarkerRemove = jest.fn();
const mockMarkerSetLngLat = jest.fn();

jest.mock('mapbox-gl', () => {
  const mapInstance = () => ({
    on: jest.fn((event: string, layerOrHandler: unknown, maybeHandler: unknown) => {
      const handler = typeof layerOrHandler === 'function' ? layerOrHandler : maybeHandler;
      if (event === 'load' && typeof handler === 'function') handler();
    }),
    addControl: jest.fn(),
    addSource: jest.fn(),
    addLayer: jest.fn(),
    getSource: jest.fn(),
    getCanvas: jest.fn(() => ({ setAttribute: jest.fn(), style: { cursor: '' } })),
    getContainer: jest.fn(() => ({ querySelectorAll: jest.fn(() => []) })),
    setFeatureState: jest.fn(),
    fitBounds: jest.fn(),
    remove: jest.fn(),
  });
  return {
    Map: jest.fn(mapInstance),
    NavigationControl: jest.fn(),
    Popup: jest.fn(() => ({
      setLngLat: jest.fn().mockReturnThis(),
      setHTML: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
      remove: jest.fn(),
    })),
    Marker: jest.fn(() => {
      const marker: Record<string, unknown> = {};
      marker.setLngLat = jest.fn((lngLat: unknown) => {
        mockMarkerSetLngLat(lngLat);
        return marker;
      });
      marker.setPopup = jest.fn(() => marker);
      marker.addTo = jest.fn(() => marker);
      marker.remove = () => mockMarkerRemove();
      return marker;
    }),
    LngLatBounds: jest.fn(() => ({ extend: jest.fn().mockReturnThis(), isEmpty: jest.fn(() => false) })),
    accessToken: '',
  };
});

global.fetch = jest.fn();

const emptyGeoJSON = { type: 'FeatureCollection', features: [] };

function routeFetches(): string[] {
  return (global.fetch as jest.Mock).mock.calls
    .map(([url]) => String(url))
    .filter((url) => url.includes('service_pattern'));
}

describe('RouteMap on the licence page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    (global.fetch as jest.Mock).mockImplementation((url: string) =>
      Promise.resolve({
        ok: true,
        json: async () => (String(url).includes('real-time') ? {} : emptyGeoJSON),
      }),
    );
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('requests service patterns by licence number, without a revision', async () => {
    render(<RouteMap mapboxToken="t" licenceNumber="PD0000001" />);
    await waitFor(() => expect(routeFetches()).toHaveLength(1));
    const params = new URL(routeFetches()[0], 'http://localhost').searchParams;
    expect(params.get('licence_number')).toBe('PD0000001');
    expect(params.has('revision')).toBe(false);
    expect(params.has('registration_number')).toBe(false);
  });

  it('sends the visible registration numbers and refetches when they change', async () => {
    const { rerender } = render(<RouteMap mapboxToken="t" licenceNumber="PD0000001" registrationNumbers="1 - A:1" />);
    await waitFor(() => expect(routeFetches()).toHaveLength(1));
    expect(new URL(routeFetches()[0], 'http://localhost').searchParams.get('registration_number')).toBe('1 - A:1');

    rerender(<RouteMap mapboxToken="t" licenceNumber="PD0000001" registrationNumbers="1 - A:1,2 - A:2" />);
    await waitFor(() => expect(routeFetches()).toHaveLength(2));
    expect(new URL(routeFetches()[1], 'http://localhost').searchParams.get('registration_number')).toBe(
      '1 - A:1,2 - A:2',
    );
    expect(mapboxgl.Map).toHaveBeenCalledTimes(1);
  });

  it('does not refetch when the registration numbers are unchanged', async () => {
    const { rerender } = render(<RouteMap mapboxToken="t" licenceNumber="PD0000001" registrationNumbers="a" />);
    await waitFor(() => expect(routeFetches()).toHaveLength(1));
    rerender(<RouteMap mapboxToken="t" licenceNumber="PD0000001" registrationNumbers="a" />);
    expect(routeFetches()).toHaveLength(1);
  });

  describe('live vehicles', () => {
    const liveUrl = '/api/data/browser/avl-feed/real-time-bus-location/?lineRef=1&operatorRef=ALPH&journey_code=';

    it('polls every 10 seconds, reports the update time and plots markers', async () => {
      const onLiveUpdate = jest.fn();
      (global.fetch as jest.Mock).mockImplementation((url: string) =>
        Promise.resolve({
          ok: true,
          json: async () =>
            String(url).includes('real-time')
              ? { V1: { Longitude: -1.5, Latitude: 53.8, VehicleJourneyCode: 'J1' } }
              : emptyGeoJSON,
        }),
      );
      render(<RouteMap mapboxToken="t" revisionId={1} liveLocationUrl={liveUrl} onLiveUpdate={onLiveUpdate} />);

      await waitFor(() => expect(mapboxgl.Marker).toHaveBeenCalledTimes(1));
      expect(onLiveUpdate).toHaveBeenCalledTimes(1);
      expect(onLiveUpdate.mock.calls[0][0]).toMatch(/^Last updated at - \d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2} (AM|PM)$/);

      await act(async () => {
        jest.advanceTimersByTime(10_000);
      });
      await waitFor(() => expect(onLiveUpdate).toHaveBeenCalledTimes(2));
      // The same vehicle moves its existing marker rather than creating another.
      await waitFor(() => expect(mockMarkerSetLngLat).toHaveBeenCalledTimes(2));
      expect(mapboxgl.Marker).toHaveBeenCalledTimes(1);
    });

    it('removes markers for vehicles that are no longer reported', async () => {
      let payload: Record<string, unknown> = { V1: { Longitude: -1.5, Latitude: 53.8, VehicleJourneyCode: 'J1' } };
      (global.fetch as jest.Mock).mockImplementation((url: string) =>
        Promise.resolve({ ok: true, json: async () => (String(url).includes('real-time') ? payload : emptyGeoJSON) }),
      );
      render(<RouteMap mapboxToken="t" revisionId={1} liveLocationUrl={liveUrl} />);
      await waitFor(() => expect(mapboxgl.Marker).toHaveBeenCalledTimes(1));

      payload = {};
      await act(async () => {
        jest.advanceTimersByTime(10_000);
      });
      await waitFor(() => expect(mockMarkerRemove).toHaveBeenCalledTimes(1));
    });

    it('does not poll without a live location URL', async () => {
      render(<RouteMap mapboxToken="t" revisionId={1} />);
      await waitFor(() => expect(routeFetches()).toHaveLength(1));
      expect((global.fetch as jest.Mock).mock.calls.some(([url]) => String(url).includes('real-time'))).toBe(false);
    });
  });
});
