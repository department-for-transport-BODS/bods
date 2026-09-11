import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableCreateCancelPage from './page';

const mockUseParams = jest.fn();
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
  useRouter: () => ({
    push: mockPush,
  }),
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('TimetableCreateCancelPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue({
      orgId: 'org-123',
    });
  });

  it('renders links back to form and list page', () => {
    render(<TimetableCreateCancelPage />);

    const backLink = screen.getByRole('link', { name: 'Back' });
    expect(backLink).toHaveAttribute('href', '/publish/org/org-123/dataset/timetable/new');

    const confirmLink = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmLink).toHaveAttribute('href', '/publish/org/org-123/dataset/timetable');
  });

  it('returns to the form at the top of the page', async () => {
    const user = userEvent.setup();
    render(<TimetableCreateCancelPage />);

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockPush).toHaveBeenCalledWith('/publish/org/org-123/dataset/timetable/new', { scroll: true });
  });
});