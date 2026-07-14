import { render, screen, waitFor } from '@testing-library/react';
import AVLUpdateCancelPage from './page';

const mockUseParams = jest.fn();
const mockBack = jest.fn();
const mockApiGet = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
  useRouter: () => ({
    back: mockBack,
  }),
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: (path: string) => mockApiGet(path),
  },
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('AVLUpdateCancelPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue({
      orgId: 'org-123',
      datasetId: 'dataset-456',
    });
  });

  it('navigates to review page when feed is draft', async () => {
    mockApiGet.mockResolvedValue({ status: 'draft' });

    render(<AVLUpdateCancelPage />);

    await waitFor(() => {
      const confirmLink = screen.getByRole('button', { name: 'Confirm' });
      expect(confirmLink).toHaveAttribute(
        'href',
        '/publish/org/org-123/dataset/avl/dataset-456/review',
      );
    });
  });

  it('navigates to detail page when feed is not draft', async () => {
    mockApiGet.mockResolvedValue({ status: 'published' });

    render(<AVLUpdateCancelPage />);

    await waitFor(() => {
      const confirmLink = screen.getByRole('button', { name: 'Confirm' });
      expect(confirmLink).toHaveAttribute(
        'href',
        '/publish/org/org-123/dataset/avl/dataset-456',
      );
    });
  });

  it('keeps back link pointing to update form', () => {
    render(<AVLUpdateCancelPage />);

    const backLink = screen.getByRole('link', { name: 'Back' });

    expect(backLink).toHaveAttribute(
      'href',
      '/publish/org/org-123/dataset/avl/dataset-456/update',
    );
  });
});
