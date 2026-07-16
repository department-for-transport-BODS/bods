import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PublishPage from './page';
import { getPaginated } from '@/lib/api-client';
import { useAuth } from '@/hooks/useAuth';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
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

type MockRadiosProps = {
  name: string;
  items: { value: string; children: string }[];
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  errorMessage?: string;
};

jest.mock('kainossoftwareltd-govuk-react-kainos', () => ({
  Radios: ({ name, items, value, onChange, errorMessage }: MockRadiosProps) => (
    <fieldset>
      {errorMessage && <p role="alert">{errorMessage}</p>}
      {items.map((item) => (
        <label key={item.value}>
          <input
            name={name}
            type="radio"
            value={item.value}
            checked={value === item.value}
            onChange={onChange}
          />
          {item.children}
        </label>
      ))}
    </fieldset>
  ),
}));

const dataTypeOptions = [
  {
    label: 'Timetables',
    dataType: 'timetable',
    singleOrgUrl: '/publish/org/123/dataset/timetable',
    orgSelectionUrl: '/publish/org?dataType=timetable',
  },
  {
    label: 'Automatic Vehicle Locations (AVL)',
    dataType: 'avl',
    singleOrgUrl: '/publish/org/123/dataset/avl/new',
    orgSelectionUrl: '/publish/org?dataType=avl',
  },
  {
    label: 'Fares',
    dataType: 'fares',
    singleOrgUrl: '/publish/org/123/dataset/fares',
    orgSelectionUrl: '/publish/org?dataType=fares',
  },
];

describe('PublishPage routing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows an error and does not route when no data type is selected', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
        organisation_id: 123,
      },
    });

    render(<PublishPage />);

    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Please select a data type');
    expect(getPaginated).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it.each(dataTypeOptions)(
    'routes normal organisation users directly to their $dataType dataset page',
    async ({ label, singleOrgUrl }) => {
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: true,
          is_agent_user: false,
          organisation_id: 123,
        },
      });

      render(<PublishPage />);

      await userEvent.click(screen.getByLabelText(label));
      await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

      expect(getPaginated).not.toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith(singleOrgUrl);
    },
  );

  it('routes agents with one organisation to organisation selection', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: true,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123 }],
    });

    render(<PublishPage />);

    await userEvent.click(screen.getByLabelText('Timetables'));
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(getPaginated).toHaveBeenCalledWith('/api/organisations/');
    expect(mockPush).toHaveBeenCalledWith('/publish/org?dataType=timetable');
  });

  it.each(dataTypeOptions)(
    'routes single organisation users without an organisation id using their fetched $dataType organisation',
    async ({ label, singleOrgUrl }) => {
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: true,
          is_agent_user: false,
          organisation_id: null,
        },
      });
      (getPaginated as jest.Mock).mockResolvedValue({
        results: [{ id: 123 }],
      });

      render(<PublishPage />);

      await userEvent.click(screen.getByLabelText(label));
      await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

      expect(getPaginated).toHaveBeenCalledWith('/api/organisations/');
      expect(mockPush).toHaveBeenCalledWith(singleOrgUrl);
    },
  );

  it.each(dataTypeOptions)(
    'routes users with multiple organisations to organisation selection with $dataType data type',
    async ({ label, orgSelectionUrl }) => {
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: false,
          is_agent_user: false,
          organisation_id: 123,
        },
      });
      (getPaginated as jest.Mock).mockResolvedValue({
        results: [{ id: 123 }, { id: 456 }],
      });

      render(<PublishPage />);

      await userEvent.click(screen.getByLabelText(label));
      await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

      expect(getPaginated).toHaveBeenCalledWith('/api/organisations/');
      expect(mockPush).toHaveBeenCalledWith(orgSelectionUrl);
    },
  );

  it('routes to organisation selection when organisation lookup fails', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockRejectedValue(new Error('Unable to load organisations'));

    render(<PublishPage />);

    await userEvent.click(screen.getByLabelText('Timetables'));
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(getPaginated).toHaveBeenCalledWith('/api/organisations/');
    expect(mockPush).toHaveBeenCalledWith('/publish/org?dataType=timetable');
  });
});
