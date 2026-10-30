import { render, screen, waitFor } from '@testing-library/react';
import { LicenceLineDetailContent } from './LicenceLineDetailContent';
import { ApiError, api } from '@/lib/api-client';
import { dataPath, publishPath } from '@/config/client';
import type { LicenceLineDetail } from '@/lib/operators';

const mockNotFound = jest.fn();
const mockMap = jest.fn();
const mockVisualiser = jest.fn();
let mockSearch = 'line=1&service=PD0000001:1&org_id=10';

jest.mock('next/navigation', () => ({
  notFound: () => mockNotFound(),
  useSearchParams: () => new URLSearchParams(mockSearch),
}));

jest.mock('@/lib/api-client', () => {
  class MockApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  }
  return { api: { get: jest.fn() }, ApiError: MockApiError };
});

jest.mock('@/components/data/MapboxRouteMap', () => ({
  MapboxRouteMap: (props: Record<string, unknown>) => {
    mockMap(props);
    return <div data-testid="map" />;
  },
}));

jest.mock('@/components/timetables/TimetableVisualiser', () => ({
  TimetableVisualiser: (props: Record<string, unknown>) => {
    mockVisualiser(props);
    return <div data-testid="visualiser" />;
  },
}));

const FILE = { filename: 'a.xml', startDate: '2024-01-01', endDate: '2024-12-31' };

function lineDetail(overrides: Partial<LicenceLineDetail> = {}): LicenceLineDetail {
  return {
    licenceNumber: 'PD0000001',
    lineName: '1',
    serviceCode: 'PD0000001:1',
    isLicencePage: true,
    organisation: { id: 10, name: 'Alpha Buses With A Very Long Name' },
    datasetId: 7,
    revisionId: 70,
    flags: {
      isCompleteServicePagesActive: true,
      isCompleteServicePagesRealTimeDataActive: false,
      isAvlRequireAttentionActive: true,
      isFaresRequireAttentionActive: true,
      isTimetableVisualiserActive: true,
      isSpecificFeedback: true,
    },
    serviceInScope: true,
    serviceInSeason: true,
    isAvlCompliant: true,
    isFaresCompliant: true,
    isTimetableCompliant: true,
    serviceType: 'Standard',
    bookingArrangements: null,
    bookingMethods: null,
    fares: {
      datasetId: 9,
      tariffBasis: ['Point to point', 'Flat'],
      products: [],
      validFiles: [FILE],
      futureDatedFiles: [],
      expiredFiles: [],
    },
    timetableFiles: {
      datasetId: 7,
      validFiles: [FILE],
      futureDatedFiles: [],
      expiredFiles: [],
    },
    timetable: { currDate: '2024-05-01', isTimetableInfoAvailable: true, directions: [] },
    outboundStartAndEnd: 'A to B',
    realTime: { nationalOperatorCode: 'ALPH', vehicleJourneyCodes: '' },
    ...overrides,
  };
}

function load(data: LicenceLineDetail) {
  jest.mocked(api.get).mockResolvedValue(data);
  return render(<LicenceLineDetailContent licenceNumber="PD0000001" />);
}

describe('LicenceLineDetailContent', () => {
  beforeEach(() => {
    mockSearch = 'line=1&service=PD0000001:1&org_id=10';
  });
  afterEach(() => jest.clearAllMocks());

  it('passes the page query string to the line API', async () => {
    load(lineDetail());
    await screen.findByRole('heading', { level: 1 });
    expect(api.get).toHaveBeenCalledWith(
      '/api/data/browser/operators/licence/PD0000001/line/details/?line=1&service=PD0000001%3A1&org_id=10',
    );
  });

  it('renders the licence variant: title, breadcrumbs, compliant heading and report link', async () => {
    load(lineDetail());
    const heading = await screen.findByRole('heading', { level: 1 });

    expect(heading).toHaveTextContent('1 Compliant');
    expect(heading.querySelector('.govuk-tag--green')).toBeInTheDocument();
    expect(document.title).toBe('1');
    expect(screen.getByRole('link', { name: 'Operator Profiles' })).toHaveAttribute('href', dataPath('/operators/'));
    expect(screen.getByRole('link', { name: 'Alpha Buses With A…' })).toHaveAttribute('href', dataPath('/operators/10/'));
    expect(screen.getByRole('link', { name: 'PD0000001' })).toHaveAttribute(
      'href',
      dataPath('/operators/licence/PD0000001/?org_id=10'),
    );
    expect(screen.getByRole('link', { name: 'Download compliance report' })).toHaveAttribute(
      'href',
      publishPath('/org/10/dataset/timetable/compliance-report/'),
    );
    expect(screen.getByText('Overview of the available bus open data')).toBeInTheDocument();
    expect(screen.getByText('-', { selector: '#map-updated-timestamp' })).toBeInTheDocument();
  });

  it.each([
    [{ serviceInScope: false }, 'Out of Scope', 'govuk-tag--red'],
    [{ serviceInSeason: false }, 'Out of Season', 'govuk-tag--red'],
    [{ isAvlCompliant: false }, 'Not Compliant', 'govuk-tag--red'],
  ])('shows the heading tag for %j', async (overrides, label, className) => {
    load(lineDetail(overrides));
    const heading = await screen.findByRole('heading', { level: 1 });
    const tag = heading.querySelector('.govuk-tag');
    expect(tag).toHaveTextContent(label);
    expect(tag).toHaveClass(className);
  });

  it('prefers Out of Scope over Out of Season', async () => {
    load(lineDetail({ serviceInScope: false, serviceInSeason: false }));
    const heading = await screen.findByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('Out of Scope');
  });

  it('gives the map the revision, line and service code', async () => {
    load(lineDetail());
    await screen.findByTestId('map');
    expect(mockMap).toHaveBeenLastCalledWith(
      expect.objectContaining({ revisionId: 70, lineName: '1', serviceCodes: 'PD0000001:1', liveLocationUrl: undefined }),
    );
  });

  it('omits the revision when there is no live dataset', async () => {
    load(lineDetail({ revisionId: null }));
    await screen.findByTestId('map');
    expect(mockMap).toHaveBeenLastCalledWith(expect.objectContaining({ revisionId: undefined }));
  });

  describe('live vehicle locations', () => {
    it('wires the live feed when the real time flag is on', async () => {
      load(
        lineDetail({
          flags: { ...lineDetail().flags, isCompleteServicePagesRealTimeDataActive: true },
          realTime: { nationalOperatorCode: 'ALPH,ALPB', vehicleJourneyCodes: 'J1' },
        }),
      );
      await screen.findByTestId('map');
      const props = mockMap.mock.calls.at(-1)?.[0];
      expect(props.liveLocationUrl).toBe(
        '/api/data/browser/avl-feed/real-time-bus-location/?lineRef=1&operatorRef=ALPH,ALPB&journey_code=J1',
      );
      expect(typeof props.onLiveUpdate).toBe('function');
    });

    it('skips the live feed when every operator code is blank', async () => {
      load(
        lineDetail({
          flags: { ...lineDetail().flags, isCompleteServicePagesRealTimeDataActive: true },
          realTime: { nationalOperatorCode: ' , ', vehicleJourneyCodes: '' },
        }),
      );
      await screen.findByTestId('map');
      expect(mockMap.mock.calls.at(-1)?.[0].liveLocationUrl).toBeUndefined();
    });
  });

  describe('compliance sections', () => {
    it('renders AVL, Fares and Timetable sections with Django copy', async () => {
      load(lineDetail());
      await screen.findByRole('heading', { level: 1 });

      expect(screen.getByRole('heading', { level: 2, name: 'AVL' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'Fares' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'Timetable' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Dataset ID: 9' })).toHaveAttribute('href', dataPath('/fares/dataset/9/'));
      expect(screen.getByRole('link', { name: 'Dataset ID: 7' })).toHaveAttribute(
        'href',
        dataPath('/timetable/dataset/7/'),
      );
      expect(screen.getByText('Point to point, Flat')).toBeInTheDocument();
      expect(screen.getAllByText('Current valid file(s)')).toHaveLength(2);
      expect(screen.getAllByText('Future dated file(s)')).toHaveLength(2);
      expect(screen.getAllByText('Expired file(s)')).toHaveLength(2);
    });

    it('shows N/A for empty tariff basis, products and file lists', async () => {
      load(lineDetail({ fares: { ...lineDetail().fares, tariffBasis: [], validFiles: [] } }));
      await screen.findByRole('heading', { level: 1 });
      expect(screen.getAllByText('N/A').length).toBeGreaterThanOrEqual(4);
    });

    it('shows Unpublished tags when there are no datasets', async () => {
      load(
        lineDetail({
          datasetId: null,
          fares: { ...lineDetail().fares, datasetId: null },
          isTimetableCompliant: false,
          isFaresCompliant: false,
        }),
      );
      await screen.findByRole('heading', { level: 1 });
      expect(screen.getAllByText('Unpublished')).toHaveLength(2);
      expect(screen.queryByRole('link', { name: /Dataset ID/ })).not.toBeInTheDocument();
    });

    it('hides the AVL and Fares sections when their flags are off', async () => {
      load(
        lineDetail({
          flags: { ...lineDetail().flags, isAvlRequireAttentionActive: false, isFaresRequireAttentionActive: false },
        }),
      );
      await screen.findByRole('heading', { level: 1 });
      expect(screen.queryByRole('heading', { level: 2, name: 'AVL' })).not.toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 2, name: 'Fares' })).not.toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'Timetable' })).toBeInTheDocument();
    });

    it('hides every section when the complete service pages flag is off', async () => {
      load(lineDetail({ flags: { ...lineDetail().flags, isCompleteServicePagesActive: false } }));
      await screen.findByRole('heading', { level: 1 });
      expect(screen.queryByRole('heading', { level: 2, name: 'Timetable' })).not.toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 2, name: 'AVL' })).not.toBeInTheDocument();
    });
  });

  describe('timetable visualiser and feedback', () => {
    it('passes the dataset feedback URL to the visualiser when specific feedback is on', async () => {
      load(lineDetail());
      await screen.findByTestId('visualiser');
      expect(mockVisualiser).toHaveBeenLastCalledWith(
        expect.objectContaining({
          feedbackUrl: dataPath('/timetable/dataset/7/feedback/'),
          renderEmptyDirections: false,
        }),
      );
    });

    it('uses an empty timetable and no feedback URL without a live dataset', async () => {
      load(lineDetail({ datasetId: null, timetable: null }));
      await screen.findByTestId('visualiser');
      expect(mockVisualiser).toHaveBeenLastCalledWith(
        expect.objectContaining({
          feedbackUrl: null,
          timetable: { currDate: '', isTimetableInfoAvailable: false, directions: [] },
        }),
      );
    });

    it('does not render the visualiser when its flag is off', async () => {
      load(lineDetail({ flags: { ...lineDetail().flags, isTimetableVisualiserActive: false } }));
      await screen.findByRole('heading', { level: 1 });
      expect(screen.queryByTestId('visualiser')).not.toBeInTheDocument();
    });

    it('shows the service feedback variant when the service param and flag are present', async () => {
      load(lineDetail());
      expect(await screen.findByRole('heading', { level: 2, name: 'Noticed issues with this service?' })).toBeInTheDocument();
      expect(screen.getByText(/You can select a stop code or journey code above/)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Provide feedback about this service' })).toHaveAttribute(
        'href',
        expect.stringContaining('/timetable/dataset/7/feedback/?'),
      );
    });

    it('shows the data set feedback variant without the service param', async () => {
      mockSearch = 'line=1';
      load(lineDetail());
      expect(await screen.findByRole('heading', { level: 2, name: 'Noticed issues with this data set?' })).toBeInTheDocument();
      expect(screen.queryByText(/You can select a stop code/)).not.toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Contact data set owner directly' })).toHaveAttribute(
        'href',
        dataPath('/timetable/dataset/7/feedback/'),
      );
    });

    it('has an empty feedback link without a dataset, as Django swallows NoReverseMatch', async () => {
      load(lineDetail({ datasetId: null }));
      expect(await screen.findByRole('link', { name: 'Provide feedback about this service' })).toBeInTheDocument();
    });
  });

  describe('passenger facing variant (?pf=)', () => {
    beforeEach(() => {
      mockSearch = 'line=1&service=PD0000001:1&pf=1';
    });

    it('shows "<organisation> : <line> - <start and end>" and no compliance, files or feedback', async () => {
      load(lineDetail({ isLicencePage: false }));
      const heading = await screen.findByRole('heading', { level: 1 });

      expect(heading).toHaveTextContent('Alpha Buses With A Very Long Name : 1 - A to B');
      expect(screen.queryByRole('link', { name: 'Download compliance report' })).not.toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 2, name: 'AVL' })).not.toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 2, name: 'Timetable' })).not.toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'Fares' })).toBeInTheDocument();
      expect(screen.queryByText('Current valid file(s)')).not.toBeInTheDocument();
      expect(screen.queryByText(/Noticed issues/)).not.toBeInTheDocument();
      expect(screen.queryByText('Registration number')).not.toBeInTheDocument();
    });

    it('uses the Django placeholders for a missing organisation and missing start/end', async () => {
      load(lineDetail({ isLicencePage: false, organisation: null, outboundStartAndEnd: null }));
      const heading = await screen.findByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Organisation not yet created : 1 - None');
      expect(screen.getByRole('link', { name: 'Organisation not yet created' })).toHaveAttribute('href', '#');
    });

    it('drops the start and end when no timetable info is available', async () => {
      load(lineDetail({ isLicencePage: false, timetable: null }));
      const heading = await screen.findByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Alpha Buses With A Very Long Name : 1');
      expect(heading).not.toHaveTextContent(' - ');
    });
  });

  it('shows the not-yet-created breadcrumb and no report link without an organisation', async () => {
    load(lineDetail({ organisation: null }));
    await screen.findByRole('heading', { level: 1 });
    expect(screen.getByRole('link', { name: 'Organisation not yet created' })).toHaveAttribute('href', '#');
    expect(screen.getByRole('link', { name: 'PD0000001' })).toHaveAttribute(
      'href',
      dataPath('/operators/licence/PD0000001/?org_id=None'),
    );
    expect(screen.queryByRole('link', { name: 'Download compliance report' })).not.toBeInTheDocument();
  });

  it('calls notFound() when the API returns 404', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('Not found', 404, {}));
    render(<LicenceLineDetailContent licenceNumber="NOPE" />);
    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error when the API fails', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('boom', 500, {}));
    render(<LicenceLineDetailContent licenceNumber="PD0000001" />);
    expect(await screen.findByText('Failed to load service')).toBeInTheDocument();
  });
});
