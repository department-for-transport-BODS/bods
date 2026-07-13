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
};

jest.mock('kainossoftwareltd-govuk-react-kainos', () => ({
  Radios: ({ name, items, value, onChange }: MockRadiosProps) => (
    <fieldset>
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

describe('PublishPage routing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('routes normal organisation users directly to their organisation dataset page', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
        organisation_id: 123,
      },
    });

    render(<PublishPage />);

    await userEvent.click(screen.getByLabelText('Timetables'));
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(getPaginated).not.toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable');
  });

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
});
