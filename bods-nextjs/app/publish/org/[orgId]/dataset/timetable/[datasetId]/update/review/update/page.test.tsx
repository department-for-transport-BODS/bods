import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableUpdateReviewUpdatePage from './page';
import { api } from '@/lib/api-client';
import { publishPath } from '@/config/client';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123', datasetId: '456' }),
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: jest.fn(), get: jest.fn() },
}));

describe('TimetableUpdateReviewUpdatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockResolvedValue({ urlLink: 'https://example.com/current.xml' });
    (api.post as jest.Mock).mockResolvedValue({
      redirect: '/publish/org/123/dataset/timetable/456/update/review',
    });
  });

  it('pre-fills the URL link from the draft revision, like Django', async () => {
    render(<TimetableUpdateReviewUpdatePage />);

    await waitFor(() => expect(screen.getByLabelText('URL Link')).toHaveValue('https://example.com/current.xml'));
    expect(api.get).toHaveBeenCalledWith('/api/publish/timetables/review-status/123/456/');
  });

  it('shows the Django no-selection error on the URL link field', async () => {
    render(<TimetableUpdateReviewUpdatePage />);

    await userEvent.setup().click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('link', { name: 'Please provide a file or url' })).toHaveAttribute('href', '#id_url_link');
    expect(screen.getByLabelText('URL Link').closest('#url_link-conditional')).not.toHaveClass(
      'govuk-radios__conditional--hidden',
    );
    expect(api.post).not.toHaveBeenCalled();
  });

  it('matches Django DatasetUpdateModify: title, heading and Comment/Update stepper', () => {
    render(<TimetableUpdateReviewUpdatePage />);

    expect(document.title).toBe('Update data set: upload');
    expect(screen.getByRole('heading', { level: 1, name: 'Choose how to provide your data set' })).toBeInTheDocument();
    expect(screen.getByText('1. Comment')).toBeInTheDocument();
    expect(screen.getByText('2. Update').closest('li')).toHaveClass('publish-stepper__item--selected');
    expect(screen.getByText('3. Review and publish')).toBeInTheDocument();
  });

  it('renders the Django RadioAccordion with both conditional inputs up front', () => {
    render(<TimetableUpdateReviewUpdatePage />);

    const legend = screen.getByRole('group', { name: 'Choose how to provide your data set' });
    expect(legend.closest('[data-module="app-radio-accordion"]')).not.toBeNull();
    const linkRadio = screen.getByLabelText('Provide a link to your data set');
    expect(linkRadio).toHaveAttribute('id', 'url_link-conditional-radio');
    expect(linkRadio).toHaveAttribute('name', 'selected_item');
    expect(linkRadio).toHaveAttribute('value', 'url_link-conditional');
    expect(linkRadio).toHaveAttribute('data-aria-controls', 'url_link-conditional');
    expect(screen.getByLabelText('Upload data set to Bus Open Data Service')).toHaveAttribute('value', 'upload_file-conditional');
    expect(linkRadio.closest('.govuk-radios')).toHaveClass('govuk-radios--conditional');
    expect(linkRadio.closest('.govuk-radios')).toHaveAttribute('data-module', 'govuk-radios');

    const urlInput = screen.getByLabelText('URL Link');
    const fileInput = screen.getByLabelText('Upload File');
    expect(urlInput).toHaveAttribute('name', 'url_link');
    expect(fileInput).toHaveAttribute('name', 'upload_file');
    expect(urlInput.closest('#url_link-conditional')).toHaveClass('govuk-radios__conditional--hidden');
    expect(fileInput.closest('#upload_file-conditional')).toHaveClass('govuk-radios__conditional--hidden');
  });

  it('reveals the conditional input for the chosen radio', async () => {
    render(<TimetableUpdateReviewUpdatePage />);

    await userEvent.setup().click(screen.getByLabelText('Provide a link to your data set'));

    expect(screen.getByLabelText('URL Link').closest('#url_link-conditional')).not.toHaveClass(
      'govuk-radios__conditional--hidden',
    );
    expect(screen.getByLabelText('Upload File').closest('#upload_file-conditional')).toHaveClass(
      'govuk-radios__conditional--hidden',
    );
  });

  it('shows the Django cancel step in place from the Cancel button, like DatasetUpdateModify', async () => {
    render(<TimetableUpdateReviewUpdatePage />);
    const user = userEvent.setup();
    const cancel = screen.getByRole('button', { name: 'Cancel' });

    expect(cancel.tagName).toBe('BUTTON');
    expect(cancel).toHaveAttribute('name', 'cancel');
    await user.click(cancel);

    expect(document.title).toBe('Update data set: cancel');
    expect(
      screen.getByRole('heading', { level: 1, name: 'Would you like to cancel updating this data set?' }),
    ).toBeInTheDocument();
    expect(screen.queryByText('1. Comment')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      publishPath('/org/123/dataset/timetable/456/update/review/'),
    );

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(screen.getByRole('group', { name: 'Choose how to provide your data set' })).toBeInTheDocument();
    expect(document.title).toBe('Update data set: upload');
  });

  it('posts is_update and returns to update/review', async () => {
    render(<TimetableUpdateReviewUpdatePage />);
    const user = userEvent.setup();
    const file = new File(['<xml />'], 'replacement.xml', { type: 'text/xml' });

    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload File'), file);
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const formData = (api.post as jest.Mock).mock.calls[0][1] as FormData;
    expect(api.post).toHaveBeenCalledWith('/api/publish/timetables/update/123/456/', expect.any(FormData));
    expect(formData.get('selected_item')).toBe('upload_file-conditional');
    expect(formData.get('is_update')).toBe('true');
    expect(formData.get('upload_file')).toBe(file);
    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/update/review');
  });

  it('falls back to update/review when the API returns no redirect', async () => {
    (api.post as jest.Mock).mockResolvedValue({});
    render(<TimetableUpdateReviewUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload File'), new File(['<xml />'], 'a.xml', { type: 'text/xml' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/update/review'),
    );
  });
});
