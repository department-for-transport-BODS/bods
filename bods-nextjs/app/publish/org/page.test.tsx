import { render, screen } from '@testing-library/react';
import { waitFor } from '@testing-library/dom';
import userEvent from '@testing-library/user-event';
import SelectOrgPage from './page';
import { getPaginated } from '@/lib/api-client';
import { useAuth } from '@/hooks/useAuth';

const mockPush = jest.fn();
const mockUseSearchParams = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/lib/api-client', () => ({
  getPaginated: jest.fn(),
}));

const dataTypeOptions = [
  { dataType: 'timetable', expectedUrl: '/publish/org/123/dataset/timetable' },
  { dataType: 'avl', expectedUrl: '/publish/org/123/dataset/avl' },
  { dataType: 'fares', expectedUrl: '/publish/org/123/dataset/fares' },
];

describe('SelectOrgPage routing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams('dataType=timetable'));
  });

  it('keeps non-single organisation users on organisation selection', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: 'OrganisationOne' }],
    });

    render(<SelectOrgPage />);

    await waitFor(() => expect(screen.getByText('OrganisationOne')).toBeInTheDocument());
    expect(mockPush).not.toHaveBeenCalled();
  });

  it.each(dataTypeOptions)(
    'routes single organisation users directly to their $dataType dataset page',
    async ({ dataType, expectedUrl }) => {
      mockUseSearchParams.mockReturnValue(new URLSearchParams(`dataType=${dataType}`));
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: true,
          is_agent_user: false,
          organisation_id: 123,
        },
      });
      (getPaginated as jest.Mock).mockResolvedValue({
        results: [{ id: 123, name: 'OrganisationOne' }],
      });

      render(<SelectOrgPage />);

      await waitFor(() => expect(mockPush).toHaveBeenCalledWith(expectedUrl));
    },
  );

  it('defaults single organisation users directly to the timetable dataset page', async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: 'OrganisationOne' }],
    });

    render(<SelectOrgPage />);

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable'),
    );
  });

  it.each(dataTypeOptions)(
    'routes selected organisations to the requested $dataType dataset page',
    async ({ dataType, expectedUrl }) => {
      mockUseSearchParams.mockReturnValue(new URLSearchParams(`dataType=${dataType}`));
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: false,
          is_agent_user: false,
          organisation_id: 123,
        },
      });
      (getPaginated as jest.Mock).mockResolvedValue({
        results: [{ id: 123, name: 'OrganisationOne' }],
      });

      render(<SelectOrgPage />);

      await userEvent.click(await screen.findByRole('button', { name: 'OrganisationOne' }));

      expect(mockPush).toHaveBeenCalledWith(expectedUrl);
    },
  );

  it('defaults selected organisations to the timetable dataset page', async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: 'OrganisationOne' }],
    });

    render(<SelectOrgPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'OrganisationOne' }));

    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable');
  });
});
