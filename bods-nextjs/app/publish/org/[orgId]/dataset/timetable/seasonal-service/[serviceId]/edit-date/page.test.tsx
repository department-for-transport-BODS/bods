import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SeasonalServiceEditDatePage from './page';
import { ApiError, api } from '@/lib/api-client';

const mockPush = jest.fn();
let mockSearch = '';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '55', serviceId: '7' }),
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(mockSearch),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  ...jest.requireActual('@/lib/api-client'),
  api: { get: jest.fn(), post: jest.fn() },
}));

const detail = {
  organisationId: 55,
  organisationName: 'ZZ Org',
  isAgentUser: false,
  id: 7,
  licenceNumber: 'ZZ0000001',
  registrationCode: 100,
  serviceCode: 'ZZ0000001/100',
  start: '2026-11-12',
  end: '2027-02-10',
  serviceBegins: '12/11/2026',
  serviceEnds: '10/02/2027',
};

describe('Seasonal services - edit dates page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = 'page=3';
    (api.get as jest.Mock).mockResolvedValue(detail);
    (api.post as jest.Mock).mockResolvedValue({ id: 7 });
  });

  it('shows the licence and service code and pre-fills the dates', async () => {
    render(<SeasonalServiceEditDatePage />);

    expect(await screen.findByLabelText('Service begins on')).toHaveValue('2026-11-12');
    expect(screen.getByLabelText('Service ends on')).toHaveValue('2027-02-10');
    expect(screen.getByText('PSV Licence Number')).toBeInTheDocument();
    expect(screen.getByText('ZZ0000001')).toBeInTheDocument();
    expect(screen.getByText('Service code')).toBeInTheDocument();
    expect(screen.getByText('ZZ0000001/100')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Edit dates' })).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/api/publish/seasonal-services/55/7/');
  });

  it('cancels back to the list on the same page', async () => {
    render(<SeasonalServiceEditDatePage />);

    expect(await screen.findByRole('link', { name: 'Cancel' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/55/dataset/timetable/seasonal-service/?page=3&'),
    );
  });

  it('saves the new dates and returns to the list', async () => {
    render(<SeasonalServiceEditDatePage />);

    const end = await screen.findByLabelText('Service ends on');
    await userEvent.clear(end);
    await userEvent.type(end, '2027-03-01');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/publish/seasonal-services/55/7/update/', {
        start: '2026-11-12',
        end: '2027-03-01',
      }),
    );
    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining('/org/55/dataset/timetable/seasonal-service/?page=3&'),
      ),
    );
  });

  it('shows validation errors against the date fields', async () => {
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('Validation failed', 400, { end: ['Start date must be earlier than end date'] }),
    );
    render(<SeasonalServiceEditDatePage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Save' }));

    expect(await screen.findByRole('link', { name: 'Start date must be earlier than end date' })).toHaveAttribute(
      'href',
      '#id_end',
    );
    expect(document.getElementById('1_id_end-error')).toHaveTextContent('Start date must be earlier than end date');
    expect(document.title).toBe('Error: Bus Open Data Service');
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('shows an error when the service cannot be loaded', async () => {
    (api.get as jest.Mock).mockRejectedValue(new Error('Seasonal service not found'));
    render(<SeasonalServiceEditDatePage />);

    expect(await screen.findByText('Seasonal service not found')).toBeInTheDocument();
  });
});
