import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FaresUpdateReviewUpdatePage from './page';
import { api } from '@/lib/api-client';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: jest.fn() },
}));

describe('FaresUpdateReviewUpdatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockReturnValue(new Promise(() => {}));
  });

  it('starts on the upload step of a draft modification with the Comment / Update stepper', () => {
    render(<FaresUpdateReviewUpdatePage />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Choose how to provide your data set' }),
    ).toBeInTheDocument();
    expect(screen.getByText('2. Update').closest('li')).toHaveClass('publish-stepper__item--selected');
    expect(screen.queryByText('Provide a comment on what has been updated')).not.toBeInTheDocument();
    expect(document.title).toBe('Update data set: upload');
  });

  it('modifies the existing draft instead of starting a new revision', async () => {
    render(<FaresUpdateReviewUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByLabelText(/Upload data set/i));
    await user.upload(screen.getByLabelText(/Upload file/i), new File(['<xml />'], 'fares.xml', { type: 'text/xml' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const [url, formData] = (api.post as jest.Mock).mock.calls[0] as [string, FormData];
    expect(url).toBe('/api/publish/fares/update/1/9/');
    expect(formData.get('modify_draft')).toBe('true');
  });

  it('shows the cancel confirmation step', async () => {
    render(<FaresUpdateReviewUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(
      screen.getByRole('heading', { name: 'Would you like to cancel updating this data set?' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
  });
});
