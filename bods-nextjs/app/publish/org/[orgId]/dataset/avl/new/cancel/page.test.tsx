import { render, screen } from '@testing-library/react';
import AVLCreateCancelPage from './page';

const mockUseParams = jest.fn();
const mockBack = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
  useRouter: () => ({
    back: mockBack,
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

describe('AVLCreateCancelPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue({
      orgId: 'org-123',
    });
  });

  it('renders links back to form and list page', () => {
    render(<AVLCreateCancelPage />);

    const backLink = screen.getByRole('link', { name: 'Back' });
    expect(backLink).toHaveAttribute('href', '/publish/org/org-123/dataset/avl/new');

    const confirmLink = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmLink).toHaveAttribute('href', '/publish/org/org-123/dataset/avl');
  });
});
