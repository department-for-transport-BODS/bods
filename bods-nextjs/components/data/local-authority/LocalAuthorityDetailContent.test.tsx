import { render, screen, waitFor } from '@testing-library/react';
import { LocalAuthorityDetailContent } from '@/components/data/local-authority/LocalAuthorityDetailContent';
import { ApiError, api } from '@/lib/api-client';
import type { LocalAuthorityDetail } from '@/lib/local-authority';

const mockNotFound = jest.fn();
let mockSearch = 'auth_ids=%5B1%2C+2%5D';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/local-authority/detail',
  useSearchParams: () => new URLSearchParams(mockSearch),
  notFound: () => mockNotFound(),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

jest.mock('govuk-frontend', () => ({ Accordion: jest.fn() }), { virtual: true });

const mockGet = api.get as jest.Mock;

const detail = (overrides: Partial<LocalAuthorityDetail> = {}): LocalAuthorityDetail => ({
  name: 'Bournemouth Christchurch and Poole Council',
  authIds: '[1, 2]',
  isCompleteServicePagesActive: false,
  isAvlRequireAttentionActive: false,
  isFaresRequireAttentionActive: false,
  totalInScopeInSeasonServices: 25,
  servicesRequireAttentionPercentage: 40,
  totalTimetableRecordsRequiringAttention: 10,
  totalServicesRequiringAttention: null,
  totalLocationRecordsRequiringAttention: null,
  totalFaresRecordsRequiringAttention: null,
  licences: [],
  ...overrides,
});

const completeDetail = (overrides: Partial<LocalAuthorityDetail> = {}) =>
  detail({
    isCompleteServicePagesActive: true,
    totalServicesRequiringAttention: 7,
    totalLocationRecordsRequiringAttention: 3,
    totalFaresRecordsRequiringAttention: 2,
    licences: [
      { licenceNumber: 'PD0000001', operatorName: 'Operator One', licenceOrganisationId: 11, nonCompliant: true },
      { licenceNumber: 'PD0000002', operatorName: 'Operator Two', licenceOrganisationId: null, nonCompliant: false },
    ],
    ...overrides,
  });

describe('LocalAuthorityDetailContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = 'auth_ids=%5B1%2C+2%5D';
  });

  it('requests the detail API with the raw auth_ids', async () => {
    mockGet.mockResolvedValue(detail());

    render(<LocalAuthorityDetailContent />);

    await screen.findByRole('heading', { level: 1 });
    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/browser/local-authority/detail/?auth_ids=');
    expect(decodeURIComponent(url.split('auth_ids=')[1])).toBe('[1, 2]');
  });

  describe('complete service pages off', () => {
    it('renders the timetables compliance summary and both detailed exports', async () => {
      mockGet.mockResolvedValue(detail());

      render(<LocalAuthorityDetailContent />);

      expect(
        await screen.findByRole('heading', { level: 1, name: 'Bournemouth Christchurch and Poole Council' }),
      ).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: /Timetables data/ })).toHaveTextContent('Not Compliant');
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument();
      expect(screen.getByText(/Registered in scope\//)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Download detailed export' }).getAttribute('href')).toContain(
        '/local-authority/export?auth_ids=',
      );
      expect(screen.getByRole('link', { name: 'Download detailed line level export' }).getAttribute('href')).toContain(
        '/local-authority/line-level-export?auth_ids=',
      );
      expect(screen.queryByRole('link', { name: 'Download compliance report' })).not.toBeInTheDocument();
      expect(screen.queryByText('Review data accuracy')).not.toBeInTheDocument();
    });

    it('marks the authority compliant when no services need attention', async () => {
      mockGet.mockResolvedValue(detail({ servicesRequireAttentionPercentage: 0 }));

      render(<LocalAuthorityDetailContent />);

      expect(await screen.findByText('Compliant')).toBeInTheDocument();
      expect(screen.queryByText('Not Compliant')).not.toBeInTheDocument();
    });

    it('truncates the breadcrumb name like Django and links to the same query', async () => {
      mockGet.mockResolvedValue(detail());

      render(<LocalAuthorityDetailContent />);

      await screen.findByRole('heading', { level: 1 });
      expect(screen.getByRole('link', { name: 'Local Authority Profiles' })).toBeInTheDocument();
      const crumb = screen.getByRole('link', { name: 'Bournemouth Christ…' });
      expect(crumb.getAttribute('href')).toContain('/local-authority/detail?auth_ids=');
    });

    it('shows the help sidebar', async () => {
      mockGet.mockResolvedValue(detail());

      render(<LocalAuthorityDetailContent />);

      expect(await screen.findByText('Need further help?')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Contact the service desk' }).getAttribute('href')).toContain('/contact');
      expect(screen.getByRole('link', { name: 'Guide me' }).getAttribute('href')).toContain('/guide-me');
    });
  });

  describe('complete service pages on', () => {
    it('renders the overall stat, licence list and timetable section', async () => {
      mockGet.mockResolvedValue(completeDetail());

      render(<LocalAuthorityDetailContent />);

      expect(await screen.findByText('Total services that require attention')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
      expect(screen.getByText('/25')).toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 2, name: /Timetables data/ })).not.toBeInTheDocument();
      expect(screen.getByText('Review data accuracy')).toBeInTheDocument();
      expect(screen.getByText('Licence number')).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 3, name: 'Timetables data' })).toBeInTheDocument();
      expect(screen.queryByText('Location data')).not.toBeInTheDocument();
      expect(screen.queryByText('Fares data')).not.toBeInTheDocument();
      // Downloads depend on the AVL flag only (as in the Django template).
      expect(screen.getByRole('link', { name: 'Download detailed export' })).toBeInTheDocument();
    });

    it('links licences with org_id and omits it when unknown', async () => {
      mockGet.mockResolvedValue(completeDetail());

      render(<LocalAuthorityDetailContent />);

      const one = await screen.findByRole('link', { name: 'PD0000001: Operator One' });
      expect(one.getAttribute('href')).toMatch(/\/operators\/licence\/PD0000001\/\?org_id=11$/);
      const two = screen.getByRole('link', { name: 'PD0000002: Operator Two' });
      expect(two.getAttribute('href')).toMatch(/\/operators\/licence\/PD0000002\/$/);
    });

    it('shows location data and the compliance report link when the AVL flag is on', async () => {
      mockGet.mockResolvedValue(completeDetail({ isAvlRequireAttentionActive: true }));

      render(<LocalAuthorityDetailContent />);

      expect(await screen.findByRole('heading', { level: 3, name: 'Location data' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Download compliance report' }).getAttribute('href')).toContain(
        '/local-authority/compliance-report?auth_ids=',
      );
      expect(screen.queryByRole('link', { name: 'Download detailed export' })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: 'Download detailed line level export' })).not.toBeInTheDocument();
    });

    it('shows fares data when the fares flag is on', async () => {
      mockGet.mockResolvedValue(completeDetail({ isFaresRequireAttentionActive: true }));

      render(<LocalAuthorityDetailContent />);

      expect(await screen.findByRole('heading', { level: 3, name: 'Fares data' })).toBeInTheDocument();
    });
  });

  it('renders the Next.js 404 for an unknown authority', async () => {
    mockSearch = 'auth_ids=999';
    mockGet.mockRejectedValue(new ApiError('Local transport authority not found', 404, {}));

    render(<LocalAuthorityDetailContent />);

    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error for other failures', async () => {
    mockGet.mockRejectedValue(new ApiError('boom', 500, {}));

    render(<LocalAuthorityDetailContent />);

    expect(await screen.findByText('boom')).toBeInTheDocument();
  });
});
