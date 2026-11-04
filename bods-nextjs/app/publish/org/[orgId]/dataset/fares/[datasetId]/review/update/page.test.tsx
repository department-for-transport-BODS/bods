import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FaresReviewUpdatePage from './page';
import { api } from '@/lib/api-client';
import { publishPath } from '@/config/client';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: jest.fn(), get: jest.fn() },
}));

describe('FaresReviewUpdatePage (Django FaresDatasetUploadModify)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockResolvedValue({ urlLink: 'https://example.com/draft.xml' });
    (api.post as jest.Mock).mockReturnValue(new Promise(() => {}));
  });

  it('matches the Django title, heading and Describe / Provide stepper', async () => {
    render(<FaresReviewUpdatePage />);

    expect(document.title).toBe('Provide data: upload');
    expect(screen.getByRole('heading', { level: 1, name: 'Choose how to provide your data set' })).toBeInTheDocument();
    expect(screen.getByText('2. Provide data').closest('li')).toHaveClass('publish-stepper__item--selected');
    expect(screen.queryByText('1. Comment')).not.toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole('textbox', { name: 'url link' })).toHaveValue('https://example.com/draft.xml'),
    );
  });

  it('modifies the first-publish draft without a comment', async () => {
    render(<FaresReviewUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByLabelText(/Upload data set/i));
    await user.upload(screen.getByLabelText('Choose file'), new File(['<xml />'], 'fares.xml', { type: 'text/xml' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const [url, formData] = (api.post as jest.Mock).mock.calls[0] as [string, FormData];
    expect(url).toBe('/api/publish/fares/update/1/9/');
    expect(formData.get('modify_draft')).toBe('true');
    expect(formData.get('comment')).toBeNull();
  });

  it('confirms cancelling back to review', async () => {
    render(<FaresReviewUpdatePage />);

    await userEvent.setup().click(screen.getByRole('button', { name: 'Cancel' }));

    expect(document.title).toBe('Provide data: cancel');
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      publishPath('/org/1/dataset/fares/9/review/'),
    );
  });
});
