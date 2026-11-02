import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableUpdateReviewCancelPage from './page';

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

describe('TimetableUpdateReviewCancelPage', () => {
  beforeEach(() => jest.clearAllMocks());

  it('confirms cancellation to update/review and returns to the update form on cancel', async () => {
    render(<TimetableUpdateReviewCancelPage />);

    expect(screen.getByRole('heading', { name: 'Would you like to cancel updating this data set?' })).toBeInTheDocument();
    expect(screen.getByText('Any changes you have made so far will not be saved.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/456/update/review/update',
    );
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/456/update/review',
    );

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/update/review/update', {
      scroll: true,
    });
  });
});
