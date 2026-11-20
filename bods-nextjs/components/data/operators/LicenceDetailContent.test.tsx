import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { LicenceDetailContent } from './LicenceDetailContent';
import { ApiError, api } from '@/lib/api-client';
import { dataPath, wwwPath } from '@/config/client';
import type { LicenceDetail, LicenceService } from '@/lib/operators';

const mockNotFound = jest.fn();
const mockMap = jest.fn();

jest.mock('next/navigation', () => ({
  notFound: () => mockNotFound(),
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

function service(overrides: Partial<LicenceService> = {}): LicenceService {
  return {
    serviceNumber: '1',
    registrationNumber: 'PD0000001:1',
    fullRegistrationNumber: '1 - PD0000001:1',
    licenceOrganisationId: 10,
    localAuthorityIds: '5',
    isInScope: true,
    isInSeason: true,
    requiresAttention: false,
    avlRequiresAttention: false,
    faresRequiresAttention: false,
    isLabelGreen: true,
    labelStr: 'Compliant',
    ...overrides,
  };
}

function licence(overrides: Partial<LicenceDetail> = {}): LicenceDetail {
  return {
    licenceNumber: 'PD0000001',
    organisationId: 10,
    organisationName: 'Alpha Buses With A Very Long Name',
    isPrefetchComplianceReportActive: true,
    hasFranchise: false,
    hasNullLocalAuthority: false,
    localAuthorities: [{ id: 5, name: 'Kent' }],
    franchises: [],
    operators: [],
    services: [
      service(),
      service({
        serviceNumber: '2',
        registrationNumber: 'PD0000001:2',
        fullRegistrationNumber: '2 - PD0000001:2',
        requiresAttention: true,
      }),
      service({
        serviceNumber: '3',
        registrationNumber: 'PD0000001:3',
        fullRegistrationNumber: '3 - PD0000001:3',
        isInScope: false,
      }),
    ],
    ...overrides,
  };
}

function load(data: LicenceDetail) {
  jest.mocked(api.get).mockResolvedValue(data);
  return render(<LicenceDetailContent licenceNumber="PD0000001" />);
}

function rowNames(): string[] {
  return screen
    .getAllByRole('row')
    .filter((row) => row.classList.contains('licence-details-service-row') && !row.classList.contains('js-hidden'))
    .map((row) => within(row).getByRole('link').textContent ?? '');
}

describe('LicenceDetailContent', () => {
  afterEach(() => jest.clearAllMocks());

  it('requests the licence from the data-host browser API', async () => {
    load(licence());
    await screen.findByRole('heading', { level: 1 });
    expect(api.get).toHaveBeenCalledWith('/api/data/browser/operators/licence/PD0000001/');
  });

  it('renders the Django title, breadcrumbs, heading, owner row and sidebar', async () => {
    load(licence());
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Alpha Buses With A Very Long Name - PD0000001' }),
    ).toBeInTheDocument();

    expect(document.title).toBe('Operator Licence details');
    expect(screen.getByRole('link', { name: 'Operator Profiles' })).toHaveAttribute('href', dataPath('/operators/'));
    expect(screen.getByRole('link', { name: 'Alpha Buses With A…' })).toHaveAttribute(
      'href',
      dataPath('/operators/10/'),
    );
    expect(screen.getByRole('link', { name: 'PD0000001' })).toHaveAttribute(
      'href',
      dataPath('/operators/licence/PD0000001/?org_id=10'),
    );
    expect(screen.getByText('Overview of the available bus open data')).toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'Owner' })).toBeInTheDocument();
    expect(screen.getByText(/Access all data uploaded by this publisher/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Review Service Numbers' })).toBeInTheDocument();

    expect(screen.getByRole('heading', { level: 2, name: 'What you need to know' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View developer documentation' })).toHaveAttribute(
      'href',
      dataPath('/guidance/requirements/'),
    );
    expect(screen.getByRole('link', { name: 'Find out more about bus open data' })).toHaveAttribute('target', '_blank');
    expect(screen.getByRole('link', { name: 'Contact us for technical issues' })).toHaveAttribute(
      'href',
      wwwPath('/contact/'),
    );
  });

  it('falls back to "#" links when the licence has no organisation', async () => {
    load(licence({ organisationId: null, organisationName: 'No organisation' }));
    await screen.findByRole('heading', { level: 1 });
    expect(screen.getAllByRole('link', { name: 'No organisation' })[0]).toHaveAttribute('href', '#');
    expect(screen.getByRole('link', { name: 'PD0000001' })).toHaveAttribute(
      'href',
      dataPath('/operators/licence/PD0000001/?org_id=None'),
    );
  });

  describe('prefetch compliance report on', () => {
    it('lists the services with links to the line page and attention dots', async () => {
      load(licence());
      await screen.findByRole('heading', { level: 1 });

      expect(rowNames()).toEqual(['1 - PD0000001:1', '2 - PD0000001:2']);
      expect(screen.getByRole('link', { name: '1 - PD0000001:1' })).toHaveAttribute(
        'href',
        dataPath('/operators/licence/PD0000001/line/details/?org_id=10&line=1&service=PD0000001:1'),
      );
      const row = screen.getByRole('link', { name: '2 - PD0000001:2' }).closest('tr') as HTMLElement;
      expect(row.querySelectorAll('.sra-dot-red')).toHaveLength(1);
      expect(row.querySelectorAll('.sra-dot-green')).toHaveLength(2);
    });

    it('renders the filter table with Django ids, defaults and no franchise columns', async () => {
      load(licence({ hasNullLocalAuthority: true }));
      await screen.findByText('Filter services by');

      expect(screen.getByRole('columnheader', { name: 'Local transport authority' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Scope/Seasonality' })).toBeInTheDocument();
      expect(screen.queryByRole('columnheader', { name: 'Franchise' })).not.toBeInTheDocument();
      expect(screen.getByLabelText('Kent')).toHaveAttribute('id', 'lta_5');
      expect(screen.getByLabelText('Not Assigned')).toHaveAttribute('id', 'lta_blank');
      expect(screen.getByLabelText('In Scope')).toBeChecked();
      expect(screen.getByLabelText('Out of scope')).not.toBeChecked();
      expect(screen.getByLabelText('In Season')).toBeChecked();
      expect(screen.getByLabelText('Out of season')).not.toBeChecked();
    });

    it('shows franchise and operator filters when the licence has a franchise', async () => {
      load(
        licence({
          hasFranchise: true,
          franchises: [{ id: 11, name: 'Franchise Co' }],
          operators: [{ id: 10, name: 'Alpha Operator' }],
        }),
      );
      await screen.findByText('Filter services by');
      expect(screen.getByRole('columnheader', { name: 'Franchise' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Operator' })).toBeInTheDocument();
      expect(screen.getByLabelText('Franchise Co')).toHaveAttribute('id', 'franchise_11');
      expect(screen.getByLabelText('Alpha Operator')).toHaveAttribute('id', 'operator_10');
    });

    it('reveals out of scope services when that box is ticked and passes the visible rows to the map', async () => {
      load(licence());
      await screen.findByText('Filter services by');

      expect(mockMap).toHaveBeenLastCalledWith(
        expect.objectContaining({
          licenceNumber: 'PD0000001',
          registrationNumbers: '1 - PD0000001:1,2 - PD0000001:2',
        }),
      );

      fireEvent.click(screen.getByLabelText('Out of scope'));
      expect(rowNames()).toEqual(['1 - PD0000001:1', '2 - PD0000001:2', '3 - PD0000001:3']);
      await waitFor(() =>
        expect(mockMap).toHaveBeenLastCalledWith(
          expect.objectContaining({ registrationNumbers: '1 - PD0000001:1,2 - PD0000001:2,3 - PD0000001:3' }),
        ),
      );
    });

    it('treats a group with nothing ticked as everything, like Django', async () => {
      load(licence());
      await screen.findByText('Filter services by');
      fireEvent.click(screen.getByLabelText('Kent'));
      expect(rowNames()).toEqual(['1 - PD0000001:1', '2 - PD0000001:2']);
    });

    it('sorts like Django: the first click on Service Number is descending, the next ascending', async () => {
      load(licence());
      await screen.findByText('Filter services by');
      const header = screen.getByRole('columnheader', { name: /Service Number/ });
      expect(header).not.toHaveClass('sorted');

      fireEvent.click(header);
      expect(header).toHaveClass('sorted');
      expect(rowNames()).toEqual(['2 - PD0000001:2', '1 - PD0000001:1']);

      fireEvent.click(header);
      expect(rowNames()).toEqual(['1 - PD0000001:1', '2 - PD0000001:2']);
    });

    it('sorts by an attention column', async () => {
      load(licence());
      await screen.findByText('Filter services by');
      fireEvent.click(screen.getByRole('columnheader', { name: /Timetable data/ }));
      expect(rowNames()).toEqual(['1 - PD0000001:1', '2 - PD0000001:2']);
      fireEvent.click(screen.getByRole('columnheader', { name: /Timetable data/ }));
      expect(rowNames()).toEqual(['2 - PD0000001:2', '1 - PD0000001:1']);
    });

    it('shows "No Services Available" when the licence has no services', async () => {
      load(licence({ services: [] }));
      expect(await screen.findByText('No Services Available')).toBeInTheDocument();
      expect(document.getElementById('licence-services-table')).toBeNull();
    });
  });

  describe('prefetch compliance report off', () => {
    it('renders Django’s single legacy paragraph and no filters or map', async () => {
      load(licence({ isPrefetchComplianceReportActive: false }));
      await screen.findByRole('heading', { level: 1 });

      expect(screen.queryByText('Filter services by')).not.toBeInTheDocument();
      expect(screen.queryByTestId('map')).not.toBeInTheDocument();
      expect(document.getElementById('map')).toBeInTheDocument();
      const link = screen.getByRole('link', { name: '-' });
      expect(link).toHaveAttribute('href', dataPath('/operators/licence/PD0000001/line/details/?org_id=10&line=&service='));
      expect(link.parentElement).toHaveClass('border-bottom-custom');
      expect(link.parentElement?.querySelector('.govuk-tag--red')).toBeInTheDocument();
    });

    it('still shows the empty state', async () => {
      load(licence({ isPrefetchComplianceReportActive: false, services: [] }));
      expect(await screen.findByText('No Services Available')).toBeInTheDocument();
    });
  });

  it('calls notFound() for an unknown licence', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('Licence not found', 404, {}));
    render(<LicenceDetailContent licenceNumber="NOPE" />);
    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error when the API fails', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('boom', 500, {}));
    render(<LicenceDetailContent licenceNumber="PD0000001" />);
    expect(await screen.findByText('Failed to load licence')).toBeInTheDocument();
  });
});
