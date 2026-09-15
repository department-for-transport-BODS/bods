import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableUpdateCancelPage from './page';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123', datasetId: '456' }),
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('TimetableUpdateCancelPage', () => {
  beforeEach(() => jest.clearAllMocks());

  it('confirms cancellation to review and returns to update on cancel', async () => {
    render(<TimetableUpdateCancelPage />);

    expect(screen.getByRole('heading', { name: 'Would you like to cancel updating this data set?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/456/update',
    );
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/456/review',
    );

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockPush).toHaveBeenCalledWith(
      '/publish/org/123/dataset/timetable/456/update',
      { scroll: true },
    );
  });
});
