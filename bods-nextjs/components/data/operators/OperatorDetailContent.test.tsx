import { render, screen, waitFor } from '@testing-library/react';
import { OperatorDetailContent } from './OperatorDetailContent';
import { ApiError, api } from '@/lib/api-client';
import { dataPath, publishPath } from '@/config/client';
import type { OperatorDetail } from '@/lib/operators';

const mockNotFound = jest.fn();
const mockAccordionConstructor = jest.fn();

jest.mock('next/navigation', () => ({
  notFound: () => mockNotFound(),
}));

jest.mock('govuk-frontend', () => ({ Accordion: mockAccordionConstructor }), { virtual: true });

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

function operator(overrides: Partial<OperatorDetail> = {}): OperatorDetail {
  return {
    id: 12,
    name: 'Alpha Buses Limited',
    shortName: 'Alpha Buses With A Very Long Name',
    created: '2023-03-05T10:00:00Z',
    licenceNumbers: ['PD0000001', 'PD0000002'],
    nocs: ['ALPH', 'ALPB'],
    isAuthenticated: false,
    flags: {
      isCompleteServicePagesActive: false,
      isAvlRequireAttentionActive: false,
      isFaresRequireAttentionActive: false,
    },
    totalInScopeInSeasonServices: 20,
    totalServicesRequiringAttention: 4,
    timetableServicesRequiringAttentionCount: 2,
    avlServicesRequiringAttentionCount: 0,
    faresServicesRequiringAttentionCount: 3,
    servicesRequireAttentionPercentage: 10,
    avlServicesRequireAttentionPercentage: 15,
    faresServicesRequireAttentionPercentage: 30,
    faresStats: { totalDatasetCount: 5, totalFareProducts: 8 },
    faresNonCompliant: 1,
    overallPpcScore: null,
    operatorLicences: [
      { licenceNumber: 'PD0000001', operatorName: 'Alpha Buses', nonCompliant: false },
      { licenceNumber: 'PD0000002', operatorName: 'Alpha Coaches', nonCompliant: true },
    ],
    timetableFeedUrl: null,
    avlFeedUrl: null,
    faresFeedUrl: null,
    ...overrides,
  };
}

function load(data: OperatorDetail) {
  jest.mocked(api.get).mockResolvedValue(data);
  return render(<OperatorDetailContent operatorId="12" />);
}

describe('OperatorDetailContent', () => {
  afterEach(() => jest.clearAllMocks());

  it('requests the operator from the data-host browser API', async () => {
    load(operator());
    await screen.findByRole('heading', { level: 1 });
    expect(api.get).toHaveBeenCalledWith('/api/data/browser/operators/12/');
  });

  it('sets the Django title and truncates the breadcrumb to 19 characters', async () => {
    load(operator());
    await screen.findByRole('heading', { level: 1 });

    expect(document.title).toBe('Operator details');
    expect(screen.getByRole('link', { name: 'Operator Profiles' })).toHaveAttribute('href', dataPath('/operators/'));
    expect(screen.getByRole('link', { name: 'Alpha Buses With A…' })).toHaveAttribute(
      'href',
      dataPath('/operators/12/'),
    );
  });

  describe('legacy layout (complete service pages flag off)', () => {
    it('renders the contact links and organisation detail table', async () => {
      load(operator());
      expect(
        await screen.findByRole('heading', { level: 1, name: 'Alpha Buses With A Very Long Name' }),
      ).toBeInTheDocument();

      expect(screen.getByRole('link', { name: 'Contact Alpha Buses With A Very Long Name' })).toHaveAttribute(
        'href',
        dataPath('/operators/12/contact/'),
      );
      expect(screen.getByRole('link', { name: 'Download all data' })).toHaveAttribute('href', dataPath('/downloads/'));
      expect(screen.getByRole('link', { name: 'Consumer activity' })).toHaveAttribute(
        'href',
        publishPath('/org/12/dataset/data-activity/?prev=operator-detail'),
      );
      expect(screen.getByText('Organisation detail')).toBeInTheDocument();
      expect(screen.getByRole('rowheader', { name: 'Long name' })).toBeInTheDocument();
      expect(screen.getByText('Alpha Buses Limited')).toBeInTheDocument();
      expect(screen.getByText('5 March 2023')).toBeInTheDocument();
      expect(screen.getByText('PD0000002')).toBeInTheDocument();
      expect(screen.getByText('ALPB')).toBeInTheDocument();
    });

    it('shows the timetable stats, tag and export links', async () => {
      load(operator());
      await screen.findByText('Organisation detail');

      expect(screen.getAllByText('Not Compliant').length).toBeGreaterThan(0);
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('10%')).toBeInTheDocument();
      const exports = screen.getAllByRole('link', { name: 'Download detailed export' });
      expect(exports[0]).toHaveAttribute('href', publishPath('/org/12/dataset/timetable/service-codes/'));
      expect(screen.getByRole('link', { name: 'Browse Timetables data' })).toHaveAttribute(
        'href',
        dataPath('/timetable/?organisation=12&status=live'),
      );
    });

    it('shows "Pending" until a matching score exists, then the rounded score', async () => {
      const { unmount } = load(operator({ overallPpcScore: null }));
      expect(await screen.findByText('Pending')).toBeInTheDocument();
      unmount();

      load(operator({ overallPpcScore: 87 }));
      expect(await screen.findByText('87%')).toBeInTheDocument();
      expect(screen.queryByText('Pending')).not.toBeInTheDocument();
    });

    it('shows fares data sets / products / non-compliant when fares attention flag is off', async () => {
      load(operator());
      await screen.findByText('Data sets');

      expect(screen.getByText('Total number of fares products')).toBeInTheDocument();
      expect(screen.getByText('Non-compliant')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'What does this mean?' })).toHaveAttribute(
        'href',
        publishPath('/guidance/operator-requirements/?section=dataquality'),
      );
      expect(document.getElementById('attention-section')).toBeNull();
    });

    it('swaps in the attention percentages and compliance report when the flags are on', async () => {
      load(
        operator({
          flags: {
            isCompleteServicePagesActive: false,
            isAvlRequireAttentionActive: true,
            isFaresRequireAttentionActive: true,
          },
        }),
      );
      await screen.findByText('Organisation detail');

      expect(screen.queryByText('Data sets')).not.toBeInTheDocument();
      expect(document.getElementById('attention-section')).not.toBeNull();
      expect(screen.getByText('15%')).toBeInTheDocument();
      expect(screen.getByText('30%')).toBeInTheDocument();
      const exports = screen.getAllByRole('link', { name: 'Download detailed export' });
      expect(exports).toHaveLength(3);
      exports.forEach((link) =>
        expect(link).toHaveAttribute('href', publishPath('/org/12/dataset/timetable/compliance-report/')),
      );
    });

    it('invites anonymous users to register or sign in and hides feed URLs', async () => {
      load(operator());
      await screen.findByText('Use API');

      expect(screen.getByRole('link', { name: 'Register' })).toHaveAttribute('href', dataPath('/account/signup/'));
      expect(screen.getByRole('link', { name: 'sign in' })).toHaveAttribute('href', dataPath('/account/login/'));
      expect(screen.queryByText('Timetables data API feed URL')).not.toBeInTheDocument();
    });

    it('shows the three feed URLs to authenticated users instead of "Use API"', async () => {
      load(
        operator({
          isAuthenticated: true,
          timetableFeedUrl: 'https://data.example/api/v1/dataset/?organisation=12',
          avlFeedUrl: 'https://data.example/api/v1/datafeed/?operatorRef=ALPH',
          faresFeedUrl: 'https://data.example/api/v1/fares/dataset/?organisation=12',
        }),
      );
      await screen.findByText('Timetables data API feed URL');

      expect(screen.getByText('SIRI-VM - Location data API feed URL')).toBeInTheDocument();
      expect(screen.getByText('Fares data API feed URL')).toBeInTheDocument();
      expect(document.getElementById('timetable-feed-url')).toHaveTextContent(
        'https://data.example/api/v1/dataset/?organisation=12',
      );
      expect(screen.getAllByRole('button', { name: 'Copy code snippet to clipboard' })).toHaveLength(3);
      expect(screen.queryByText('Use API')).not.toBeInTheDocument();
    });
  });

  describe('complete service pages layout', () => {
    const complete = (overrides: Partial<OperatorDetail> = {}) =>
      operator({
        flags: {
          isCompleteServicePagesActive: true,
          isAvlRequireAttentionActive: true,
          isFaresRequireAttentionActive: true,
        },
        ...overrides,
      });

    it('renders the overall attention stat, review links and licence accordion', async () => {
      load(complete());
      await screen.findByText('Review data accuracy');

      expect(screen.getByRole('link', { name: 'Review consumer activity and feedback' })).toHaveAttribute(
        'href',
        publishPath('/org/12/dataset/data-activity/?prev=operator-detail'),
      );
      expect(screen.getByText('Total services that require attention')).toBeInTheDocument();
      expect(screen.getByText('/20')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Download compliance report' })).toHaveAttribute(
        'href',
        publishPath('/org/12/dataset/timetable/compliance-report/'),
      );
      expect(screen.getByText('Licence number')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'PD0000001: Alpha Buses' })).toHaveAttribute(
        'href',
        dataPath('/operators/licence/PD0000001/?org_id=12'),
      );
      expect(screen.queryByText('Organisation detail')).not.toBeInTheDocument();
    });

    it('initialises the GOV.UK licence accordion after the operator data loads', async () => {
      load(complete());
      await screen.findByText('Review data accuracy');

      const accordion = document.getElementById('accordion-default');
      expect(accordion).toHaveAttribute('data-module', 'govuk-accordion');
      expect(accordion?.querySelector('#accordion-default-heading-1')).toHaveTextContent('Licence number');
      expect(accordion?.querySelector('#accordion-default-content-1')).toBeInTheDocument();
      await waitFor(() => expect(mockAccordionConstructor).toHaveBeenCalledWith(accordion));
    });

    it('falls back to the detailed export when the AVL attention flag is off', async () => {
      load(
        complete({
          flags: {
            isCompleteServicePagesActive: true,
            isAvlRequireAttentionActive: false,
            isFaresRequireAttentionActive: true,
          },
        }),
      );
      await screen.findByText('Review data accuracy');

      expect(screen.getByRole('link', { name: 'Download detailed export' })).toHaveAttribute(
        'href',
        publishPath('/org/12/dataset/timetable/service-codes/'),
      );
      expect(screen.getAllByText('Services requiring attention')).toHaveLength(2);
    });

    it('marks each data type Compliant only when its count is zero', async () => {
      load(
        complete({
          totalServicesRequiringAttention: 0,
          timetableServicesRequiringAttentionCount: 0,
          avlServicesRequiringAttentionCount: 0,
          faresServicesRequiringAttentionCount: 5,
        }),
      );
      await screen.findByText('Review data accuracy');

      expect(screen.getAllByText('Compliant')).toHaveLength(3);
      expect(screen.getAllByText('Not Compliant')).toHaveLength(1);
    });

    it('links the browse pages for each data type', async () => {
      load(complete());
      await screen.findByText('Review data accuracy');

      expect(screen.getByRole('link', { name: 'Browse Location data' })).toHaveAttribute(
        'href',
        dataPath('/avl/?organisation=12&status=live'),
      );
      expect(screen.getByRole('link', { name: 'Browse Fares data' })).toHaveAttribute(
        'href',
        dataPath('/fares/?organisation=12&status=live'),
      );
      expect(screen.getByRole('link', { name: 'Download matching report' })).toHaveAttribute(
        'href',
        publishPath('/org/12/dataset/ppc-archive/'),
      );
    });

    it('includes the help modal copy', async () => {
      load(complete());
      await screen.findByText('Review data accuracy');

      expect(screen.getByText('Overall services require attention score')).toBeInTheDocument();
      expect(screen.getByText('Compliance of timetables data')).toBeInTheDocument();
      expect(screen.getByText('Compliance of real time data')).toBeInTheDocument();
      expect(screen.getByText('Compliance of fares data')).toBeInTheDocument();
      expect(screen.getAllByText('Licence colour indicates compliance')).toHaveLength(2);
    });
  });

  it('calls notFound() for an unknown operator', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('Operator not found', 404, {}));
    render(<OperatorDetailContent operatorId="999" />);
    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error when the API fails', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('boom', 500, {}));
    render(<OperatorDetailContent operatorId="12" />);
    expect(await screen.findByText('Failed to load operator')).toBeInTheDocument();
  });
});
