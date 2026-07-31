import { render, screen } from '@testing-library/react';
import AVLReviewPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../_components/AvlReviewPageContent', () => ({
  AvlReviewPageContent: ({ isUpdate }: { isUpdate: boolean }) => (
    <div data-testid="review-content">{isUpdate ? 'update' : 'create'}</div>
  ),
}));

describe('AVLReviewPage', () => {
  it('renders review page content in create mode', () => {
    render(<AVLReviewPage />);

    expect(screen.getByTestId('review-content')).toHaveTextContent('create');
  });
});
