import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FaresUpdateReviewUpdatePage from './page';
import { api } from '@/lib/api-client';
import { publishPath, wwwPath } from '@/config/client';

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
    await user.upload(screen.getByLabelText('Choose file'), new File(['<xml />'], 'fares.xml', { type: 'text/xml' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const [url, formData] = (api.post as jest.Mock).mock.calls[0] as [string, FormData];
    expect(url).toBe('/api/publish/fares/update/1/9/');
    expect(formData.get('selected_item')).toBe('upload_file-conditional');
    expect(formData.get('modify_draft')).toBe('true');
  });

  it('renders the Django RadioAccordion, hints and help links', () => {
    render(<FaresUpdateReviewUpdatePage />);

    expect(screen.getByRole('group', { name: 'Choose how to provide your data set' })).toBeInTheDocument();
    const urlInput = screen.getByRole('textbox', { name: 'url link' });
    expect(urlInput).toHaveAttribute('name', 'url_link');
    expect(urlInput.closest('#url_link-conditional')).toHaveClass('govuk-radios__conditional--hidden');
    expect(screen.getByLabelText('Provide a link to your data set')).toHaveAttribute('name', 'selected_item');
    expect(
      screen.getByText("Please provide a URL link where your NeTEX files are hosted. Example address: 'mybuscompany.com/fares.xml'."),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      publishPath('/guidance/operator-requirements'),
    );
    expect(screen.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute('href', wwwPath('/contact'));
  });

  it('shows the Django cancel step in place and returns to the form', async () => {
    render(<FaresUpdateReviewUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(
      screen.getByRole('heading', { level: 1, name: 'Would you like to cancel updating this data set?' }),
    ).toBeInTheDocument();
    expect(document.title).toBe('Update data set: cancel');
    expect(screen.queryByText('2. Update')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      publishPath('/org/1/dataset/fares/9/update/review/'),
    );

    await user.click(screen.getByRole('button', { name: 'Back' }));

    expect(screen.getByRole('group', { name: 'Choose how to provide your data set' })).toBeInTheDocument();
  });
});
