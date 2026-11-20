import { render, screen } from '@testing-library/react';
import TimetableUpdateReviewPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../_components/TimetableReviewPageContent', () => ({
  TimetableReviewPageContent: ({ isUpdate }: { isUpdate?: boolean }) => (
    <div data-testid="review">{isUpdate ? 'update' : 'publish'}</div>
  ),
}));

describe('TimetableUpdateReviewPage', () => {
  it('renders the shared review content in update mode', () => {
    render(<TimetableUpdateReviewPage />);

    expect(screen.getByTestId('review')).toHaveTextContent('update');
  });
});
