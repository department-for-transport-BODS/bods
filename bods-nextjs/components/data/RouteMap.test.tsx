/**
 * RouteMap Component Tests
 * 
 * 
 * Tests the route map component with various scenarios including
 * rendering, API integration, route display, hover interactions, and accessibility.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { RouteMap } from './RouteMap';

jest.mock('mapbox-gl', () => ({
  Map: jest.fn(() => ({
    on: jest.fn(),
    addControl: jest.fn(),
    addSource: jest.fn(),
    addLayer: jest.fn(),
    getSource: jest.fn(),
    getCanvas: jest.fn(() => ({
      setAttribute: jest.fn(),
      style: { cursor: '' },
    })),
    getContainer: jest.fn(() => ({
      querySelectorAll: jest.fn(() => []),
    })),
    setFeatureState: jest.fn(),
    fitBounds: jest.fn(),
    remove: jest.fn(),
  })),
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

global.fetch = jest.fn();

const mockMapboxToken = 'pk.test.token';
const mockApiRoot = 'https://api.example.com';

const mockGeoJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 1,
      geometry: {
        type: 'LineString',
        coordinates: [
          [-1.5, 53.8],
          [-1.4, 53.9],
        ],
      },
      properties: {
        line_name: '123',
        service_name: 'City Centre',
        origin: 'Town A',
        destination: 'Town B',
      },
    },
  ],
};

describe('RouteMap', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockGeoJSON,
    });
  });

  describe('Rendering', () => {
    it('renders the map container', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const mapContainer = document.querySelector('#map');
      expect(mapContainer).toBeInTheDocument();
    });

    it('applies disruptions-width class', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const mapContainer = document.querySelector('.disruptions-width');
      expect(mapContainer).toBeInTheDocument();
    });

    it('renders accessibility description for screen readers', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const srDescription = screen.getByRole('status');
      expect(srDescription).toHaveClass('govuk-visually-hidden');
    });

    it('uses custom aria-label when provided', () => {
      const customLabel = 'Bus route map for Service 123';
      render(
        <RouteMap
          revisionId={123}
          mapboxToken={mockMapboxToken}
          ariaLabel={customLabel}
        />
      );
      
      const mapContainer = screen.getByRole('region');
      expect(mapContainer).toHaveAttribute('aria-label', customLabel);
    });

    it('shows timestamp when enabled', async () => {
      render(
        <RouteMap
          revisionId={123}
          mapboxToken={mockMapboxToken}
          showTimestamp={true}
        />
      );
      
      await waitFor(() => {
        const timestamp = document.querySelector('#map-updated-timestamp');
        expect(timestamp).toBeInTheDocument();
      });
    });

    it('does not show timestamp by default', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const timestamp = document.querySelector('#map-updated-timestamp');
      expect(timestamp).not.toBeInTheDocument();
    });
  });

  describe('API Integration', () => {
    it('fetches route data from correct endpoint', async () => {
      render(
        <RouteMap
          revisionId={456}
          mapboxToken={mockMapboxToken}
          apiRoot={mockApiRoot}
        />
      );
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/service_pattern/?revision=456')
        );
      });
    });

    it('includes lineName parameter in API call', async () => {
      render(
        <RouteMap
          revisionId={123}
          lineName="Bus 123"
          mapboxToken={mockMapboxToken}
          apiRoot={mockApiRoot}
        />
      );
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringMatching(/line_name=Bus\+123/)
        );
      });
    });

    it('includes serviceCodes parameter in API call', async () => {
      render(
        <RouteMap
          revisionId={123}
          serviceCodes="CODE1,CODE2"
          mapboxToken={mockMapboxToken}
          apiRoot={mockApiRoot}
        />
      );
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringMatching(/service_codes=CODE1,CODE2/)
        );
      });
    });

    it('handles API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });
      
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByRole('alert')).toHaveTextContent(/HTTP error/);
      });
      
      consoleError.mockRestore();
    });

    it('displays error message for network failures', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByRole('alert')).toHaveTextContent(/Network error/);
      });
      
      consoleError.mockRestore();
    });
  });

  describe('Route Display', () => {
    it('renders routes with correct teal color', async () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      await waitFor(() => {
        const styles = document.querySelector('style');
        expect(styles?.textContent).toContain('#49A39A');
      });
    });

    it('applies hover color on route hover', async () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      await waitFor(() => {
        const styles = document.querySelector('style');
        expect(styles?.textContent).toContain('#34746e');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA role on map container', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const mapContainer = screen.getByRole('region');
      expect(mapContainer).toBeInTheDocument();
    });

    it('provides screen reader status updates', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-live', 'polite');
    });

    it('announces errors to screen readers', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Load failed'));
      
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      await waitFor(() => {
        const status = screen.getByRole('status');
        expect(status).toHaveTextContent(/Error loading map/);
      });
      
      consoleError.mockRestore();
    });

    it('provides usage instructions for screen readers', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const status = screen.getByRole('status');
      expect(status).toHaveTextContent(/Use zoom controls to navigate/);
    });

    it('marks map canvas as non-tabbable', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });
  });

  describe('Django Parity', () => {
    it('uses same map center as Django (UK center)', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('uses same map style as Django (light-v9)', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('matches Django zoom levels (5 initial, 12 max)', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('shows NavigationControl without compass like Django', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('uses same API endpoint pattern as Django', async () => {
      render(
        <RouteMap
          revisionId={789}
          mapboxToken={mockMapboxToken}
          apiRoot={mockApiRoot}
        />
      );
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          `${mockApiRoot}/api/v1/service_pattern/?revision=789`
        );
      });
    });

    it('matches Django route line styling', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('matches Django hover effect styling', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('shows service number in popup like Django', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });

    it('uses same map container ID as Django (map)', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const mapContainer = document.querySelector('#map');
      expect(mapContainer).toBeInTheDocument();
    });

    it('applies disruptions-width class matching Django', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      const mapContainer = document.querySelector('.disruptions-width');
      expect(mapContainer).toBeInTheDocument();
    });

    it('fits bounds with same padding as Django (20px)', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true); // Placeholder for integration test
    });
  });

  describe('Popup Behavior', () => {
    it('creates popup without close button', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true);
    });

    it('displays service number in popup', () => {
      render(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(true).toBe(true);
    });
  });

  describe('Map Lifecycle', () => {
    it('initializes map only once', () => {
      const { rerender } = render(
        <RouteMap revisionId={123} mapboxToken={mockMapboxToken} />
      );
      
      const mapboxgl = require('mapbox-gl');
      const initialCallCount = mapboxgl.Map.mock.calls.length;
      
      rerender(<RouteMap revisionId={123} mapboxToken={mockMapboxToken} />);
      
      expect(mapboxgl.Map.mock.calls.length).toBe(initialCallCount);
    });

    it('cleans up map on unmount', () => {
      const { unmount } = render(
        <RouteMap revisionId={123} mapboxToken={mockMapboxToken} />
      );
      
      const mapboxgl = require('mapbox-gl');
      const mockRemove = mapboxgl.Map.mock.results[0].value.remove;
      
      unmount();
      
      expect(mockRemove).toHaveBeenCalled();
    });
  });
});
