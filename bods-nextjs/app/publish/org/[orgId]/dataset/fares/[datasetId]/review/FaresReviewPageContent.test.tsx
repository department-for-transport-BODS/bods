import { render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import mapboxgl from 'mapbox-gl';
import { api } from '@/lib/api-client';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import FaresReviewPage from './FaresReviewPageContent';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useDatasetReview', () => ({
  useDatasetReview: jest.fn(),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

const mockMapOn = jest.fn();

jest.mock('mapbox-gl', () => ({
  Map: jest.fn(() => ({
    on: mockMapOn,
    addControl: jest.fn(),
    addSource: jest.fn(),
    addLayer: jest.fn(),
    fitBounds: jest.fn(),
    getCanvas: jest.fn(() => ({ style: { cursor: '' } })),
    remove: jest.fn(),
  })),
  NavigationControl: jest.fn(),
  Popup: jest.fn(() => ({
    setLngLat: jest.fn().mockReturnThis(),
    setText: jest.fn().mockReturnThis(),
    addTo: jest.fn().mockReturnThis(),
    remove: jest.fn(),
  })),
  LngLatBounds: jest.fn(() => ({
    extend: jest.fn().mockReturnThis(),
    isEmpty: jest.fn(() => false),
  })),
  accessToken: '',
}));

const mockUseDatasetReview = useDatasetReview as jest.Mock;
const mockGet = api.get as jest.Mock;

const baseStatus = {
  datasetId: 9,
  revisionId: 42,
  status: 'success',
  progress: 100,
  loading: false,
  name: 'Fares data set',
  ownerName: 'Test Org',
  lastModified: '2026-08-10T10:33:33Z',
  lastModifiedUser: null,
  error: null,
  errorDescription: null,
  schemaValidationReportUrl: null,
  isFaresValidatorActive: true,
  validatorError: false,
  schemaError: false,
  validationReportUrl: '//publish.example/org/1/dataset/fares-validator/42/export/',
};

const renderPage = (status: Record<string, unknown> | null, isInitialLoading = false) => {
  mockUseDatasetReview.mockReturnValue({
    statusData: status,
    progress: 50,
    isInitialLoading,
    errorMessage: '',
    setErrorMessage: jest.fn(),
  });
  return render(<FaresReviewPage mapboxToken="pk.test" />);
};

describe('FaresReviewPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Keep the map fetch pending unless a test needs it, so it can't update state after a test ends.
    mockGet.mockReturnValue(new Promise(() => {}));
  });

  it('shows the heading in its own row followed by a section break', () => {
    const { container } = renderPage(baseStatus);

    const heading = screen.getByRole('heading', { level: 1, name: 'Review and publish' });
    expect(heading.closest('.govuk-grid-row')?.nextElementSibling).toHaveClass(
      'govuk-section-break--visible',
    );
    expect(container.querySelector('#preview-section')).toBeInTheDocument();
  });

  it('preserves the existing headings while processing without adding the section break', () => {
    const { container } = renderPage({ ...baseStatus, loading: true });

    expect(screen.getByRole('heading', { level: 1, name: 'Review and publish' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Your data is being processed' })).toBeInTheDocument();
    expect(container.querySelector('hr')).not.toBeInTheDocument();
  });

  it.each([
    [{ validatorError: false, schemaError: false }, 'Validation Check - Passed'],
    [{ validatorError: true, schemaError: false }, 'Validation Check - Failed'],
    [{ validatorError: false, schemaError: true }, 'Validation Check - Passed with issues'],
    [{ validatorError: true, schemaError: true }, 'Validation check - Failed'],
  ])('shows the validation check panel for %o', (flags, expectedHeading) => {
    renderPage({
      ...baseStatus,
      ...flags,
      schemaValidationReportUrl: flags.schemaError ? '//publish.example/fares-csv' : null,
    });

    expect(screen.getByRole('heading', { level: 2, name: expectedHeading })).toBeInTheDocument();
    expect(screen.queryAllByRole('link', { name: 'Download validation report' })).toHaveLength(
      flags.validatorError ? 1 : 0,
    );
    expect(screen.queryAllByRole('link', { name: 'Download schema validation report' })).toHaveLength(
      flags.schemaError ? 1 : 0,
    );
  });

  it('does not show the validation check panel when the fares validator flag is off', () => {
    renderPage({ ...baseStatus, isFaresValidatorActive: false });

    expect(screen.queryByRole('heading', { name: /Validation Check/i })).not.toBeInTheDocument();
  });

  it('loads fare stops from the data host and shows stop details on hover', async () => {
    mockGet.mockResolvedValue({
      features: [
        {
          geometry: { type: 'Point', coordinates: [-0.4, 51.9] },
          properties: { id: 1, atco_code: '0200A', common_name: 'High Street' },
        },
      ],
    });
    renderPage(baseStatus);

    await waitFor(() => expect(mapboxgl.Map).toHaveBeenCalled());
    expect(mockGet).toHaveBeenCalledWith('/api/data/app/fare_stops/?revision=42');
    expect(mockMapOn).toHaveBeenCalledWith('mouseenter', 'stop-points', expect.any(Function));
    expect(mockMapOn).toHaveBeenCalledWith('mouseleave', 'stop-points', expect.any(Function));

    const mouseEnter = mockMapOn.mock.calls.find(([event]) => event === 'mouseenter')[2];
    mouseEnter({
      lngLat: { lng: -0.4, lat: 51.9 },
      features: [{ properties: { atco_code: '0200A', common_name: 'High Street' } }],
    });
    const popup = (mapboxgl.Popup as unknown as jest.Mock).mock.results[0].value;
    expect(popup.setText).toHaveBeenCalledWith('Atco: 0200A, Name: High Street');
  });

  it('renders upload error messages while preserving the existing surrounding content', () => {
    const { container } = renderPage({
      ...baseStatus,
      status: 'error',
      error: 'XML_SYNTAX_ERROR',
      errorDescription: "The dataset contains an XML file which couldn't be parsed <strong>Invalid elements</strong>",
    });

    const errorSummary = screen.getByRole('alert');
    expect(within(errorSummary).getByText('Supplied data set has failed to upload')).toBeInTheDocument();
    expect(within(errorSummary).getByText(/couldn't be parsed/)).toBeInTheDocument();
    expect(within(errorSummary).getByText('Invalid elements').tagName).toBe('STRONG');

    const datasetName = screen.getByRole('heading', { level: 2, name: 'Fares data set' });
    expect(errorSummary.compareDocumentPosition(datasetName) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    expect(screen.getByText('Data set ID')).toBeInTheDocument();
    expect(container.querySelector('.review-map-placeholder')).toBeInTheDocument();
    expect(screen.getByText('Accepted file formats include .xml (NeTEx).')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Delete data' })).toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/data/app/fare_stops/?revision=42');
    const divider = container.querySelector('hr');
    expect(divider).toHaveClass('govuk-section-break--visible');
    expect(divider!.compareDocumentPosition(errorSummary) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('shows the schema validation failure panel for schema errors', () => {
    renderPage({
      ...baseStatus,
      status: 'error',
      error: 'SCHEMA_ERROR',
      errorDescription: 'Validation Failed For Fares.Xml',
      schemaValidationReportUrl: '//publish.example/fares-csv',
    });

    expect(screen.getByRole('heading', { name: '3a Validation Check - Failed' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download schema validation report' })).toHaveAttribute(
      'href',
      '//publish.example/fares-csv',
    );
    expect(screen.getByRole('link', { name: 'guidance.' })).toHaveAttribute(
      'href',
      expect.stringContaining('/guidance/operator-requirements?section=dataquality'),
    );
    expect(screen.queryByText('Supplied data set has failed to upload')).not.toBeInTheDocument();
  });

  it('shows the stored antivirus message for suspicious files', () => {
    renderPage({
      ...baseStatus,
      status: 'error',
      error: 'SUSPICIOUS_FILE',
      errorDescription: 'Anti-Virus Alert Triggered For File Fares.Xml.',
    });

    expect(screen.getByText('Anti-Virus Alert Triggered For File Fares.Xml.')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'contact support' })).not.toBeInTheDocument();
  });

  it('links the suspicious file fallback message to the contact page', () => {
    renderPage({
      ...baseStatus,
      status: 'error',
      error: 'SUSPICIOUS_FILE',
      errorDescription:
        'Our antivirus scan detected an issue with your dataset. If you believe this to be wrong, please <a class="govuk-link" href="{support_url}">contact support</a>.',
    });

    expect(screen.getByRole('link', { name: 'contact support' })).toHaveAttribute('href', '/contact');
    expect(screen.queryByText(/\{support_url\}/)).not.toBeInTheDocument();
  });
});
