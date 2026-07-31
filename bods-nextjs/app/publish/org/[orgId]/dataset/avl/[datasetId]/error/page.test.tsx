import { render, screen } from '@testing-library/react';
import AVLErrorPage from './page';

const mockUseParams = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('AVLErrorPage', () => {
  beforeEach(() => {
    mockUseParams.mockReturnValue({
      orgId: 'org-123',
      datasetId: 'dataset-456',
    });
  });

  it('renders error message and review page link', () => {
    render(<AVLErrorPage />);

    expect(screen.getByText('Your changes could not be published')).toBeInTheDocument();

    const link = screen.getByRole('button', { name: 'Go back to review page' });
    expect(link).toHaveAttribute('href', '/publish/org/org-123/dataset/avl/dataset-456/review');
  });
});
