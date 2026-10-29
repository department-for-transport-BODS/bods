import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { api } from '@/lib/api-client';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import FaresCreatePage from './page';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useDatasetReview', () => ({
  useDatasetReview: jest.fn(),
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: jest.fn() },
}));

const mockPost = api.post as jest.Mock;
const mockUseDatasetReview = useDatasetReview as jest.Mock;

describe('FaresCreatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseDatasetReview.mockReturnValue({
      statusData: null,
      progress: 20,
      errorMessage: '',
    });
  });

  it('shows processing progress on part 2 and polls the created fares dataset', async () => {
    mockPost.mockResolvedValue({
      redirect: '/publish/org/1/dataset/fares/42/review',
    });
    const { container } = render(<FaresCreatePage />);

    fireEvent.change(screen.getByLabelText('Data set description'), {
      target: { value: 'Fares description' },
    });
    fireEvent.change(screen.getByLabelText('Data set short description'), {
      target: { value: 'Fares data' },
    });
    fireEvent.submit(container.querySelector('form')!);

    fireEvent.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    fireEvent.change(screen.getByLabelText('Choose file'), {
      target: { files: [new File(['fares'], 'fares.zip')] },
    });
    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Your data is being processed' })).toBeInTheDocument();
    });
    expect(screen.getByText('20%')).toBeInTheDocument();
    expect(screen.getByText('2. Provide data')).toBeInTheDocument();
    expect(mockUseDatasetReview).toHaveBeenLastCalledWith(
      '42',
      '/api/publish/fares/review-status/1/42/',
      'Unable to check processing status. Please refresh and try again.',
      '',
      { enabled: true },
    );
  });
});
