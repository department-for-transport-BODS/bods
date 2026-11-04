import { render, screen } from '@testing-library/react';
import TimetableReviewPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../_components/TimetableReviewPageContent', () => ({
  TimetableReviewPageContent: ({ isUpdate }: { isUpdate?: boolean }) => (
    <div data-testid="review">{isUpdate ? 'update' : 'publish'}</div>
  ),
}));

describe('TimetableReviewPage', () => {
  it('renders the shared review content in first-publish mode', () => {
    render(<TimetableReviewPage />);

    expect(screen.getByTestId('review')).toHaveTextContent('publish');
  });
});
