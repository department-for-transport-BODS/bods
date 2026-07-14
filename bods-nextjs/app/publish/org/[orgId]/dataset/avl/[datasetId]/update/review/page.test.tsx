import { render, screen } from '@testing-library/react';
import AVLUpdateReviewPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../_components/AvlReviewPageContent', () => ({
  AvlReviewPageContent: ({ isUpdate }: { isUpdate: boolean }) => (
    <div data-testid="review-content">{isUpdate ? 'update' : 'create'}</div>
  ),
}));

describe('AVLUpdateReviewPage', () => {
  it('renders review page content in update mode', () => {
    render(<AVLUpdateReviewPage />);

    expect(screen.getByTestId('review-content')).toHaveTextContent('update');
  });
});
