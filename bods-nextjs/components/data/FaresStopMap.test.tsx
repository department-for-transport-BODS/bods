import { render, waitFor } from '@testing-library/react';
import mapboxgl from 'mapbox-gl';
import { FaresStopMap } from './FaresStopMap';

jest.mock('mapbox-gl/dist/mapbox-gl.css', () => ({}), { virtual: true });

const mockMap = {
  on: jest.fn(),
  addControl: jest.fn(),
  addSource: jest.fn(),
  addLayer: jest.fn(),
  fitBounds: jest.fn(),
  remove: jest.fn(),
  getCanvas: jest.fn(() => ({
    setAttribute: jest.fn(),
    style: { cursor: '' },
  })),
  getContainer: jest.fn(() => ({ querySelectorAll: jest.fn(() => []) })),
};

jest.mock('mapbox-gl', () => ({
  Map: jest.fn(),
  NavigationControl: jest.fn(),
  Popup: jest.fn(() => ({
    setLngLat: jest.fn().mockReturnThis(),
    setHTML: jest.fn().mockReturnThis(),
    addTo: jest.fn().mockReturnThis(),
    remove: jest.fn(),
  })),
  LngLatBounds: jest.fn(() => ({
    extend: jest.fn().mockReturnThis(),
    isEmpty: jest.fn(() => false),
  })),
  accessToken: '',
}));

const mockFetch = jest.fn();

const stops = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-1.5, 53.8] },
      properties: { atco_code: 'A1', common_name: 'Stop' },
    },
  ],
};

describe('FaresStopMap', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (mapboxgl.Map as unknown as jest.Mock).mockImplementation(() => mockMap);
    mockMap.on.mockImplementation((event: string, layerOrHandler: unknown, maybeHandler?: unknown) => {
      const handler = typeof layerOrHandler === 'function' ? layerOrHandler : maybeHandler;
      if (event === 'load' && typeof handler === 'function') handler();
    });
    global.fetch = mockFetch as unknown as typeof fetch;
    mockFetch.mockResolvedValue({ ok: true, json: async () => stops });
  });

  it('renders Django’s #map container and creates the map with the Django style, centre and zoom', () => {
    const { container } = render(<FaresStopMap revisionId={21} mapboxToken="pk.test" />);

    expect(container.querySelector('#map.disruptions-width')).not.toBeNull();
    expect(mapboxgl.accessToken).toBe('pk.test');
    expect(mapboxgl.Map).toHaveBeenCalledWith(
      expect.objectContaining({
        style: 'mapbox://styles/mapbox/light-v9',
        center: [-1.1743, 52.3555],
        zoom: 5,
      }),
    );
  });

  it('loads the live revision’s stops from the data-host fare_stops API and draws them as teal dots', async () => {
    render(<FaresStopMap revisionId={21} mapboxToken="pk.test" />);

    await waitFor(() => expect(mockMap.addLayer).toHaveBeenCalled());
    expect(String(mockFetch.mock.calls[0][0])).toMatch(/\/api\/data\/app\/fare_stops\/\?revision=21$/);
    expect(mockMap.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'circle',
        paint: { 'circle-color': '#49A39A', 'circle-radius': 5 },
      }),
    );
    expect(mockMap.fitBounds).toHaveBeenCalledWith(expect.anything(), {
      padding: 20,
    });
  });

  it('draws nothing when the stops request fails', async () => {
    mockFetch.mockResolvedValue({ ok: false, json: async () => ({}) });

    render(<FaresStopMap revisionId={21} mapboxToken="pk.test" />);

    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    expect(mockMap.addLayer).not.toHaveBeenCalled();
  });

  it('removes the map on unmount', () => {
    const { unmount } = render(<FaresStopMap revisionId={21} mapboxToken="pk.test" />);

    unmount();

    expect(mockMap.remove).toHaveBeenCalled();
  });
});
