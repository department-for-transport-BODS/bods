import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetablePublishPage from './page';
import { api } from '@/lib/api-client';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: () => null }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    post: jest.fn(),
  },
}));

const fillDescriptionStep = async () => {
  await userEvent.type(screen.getByLabelText('Data set description'), 'A useful timetable');
  await userEvent.type(screen.getByLabelText('Data set short description'), 'Timetable');
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
};

const xmlFile = new File(['<xml />'], 'timetable.xml', { type: 'text/xml' });

const provideViaLink = async () => {
  await userEvent.click(screen.getByLabelText('Provide a link to your data set'));
  await userEvent.type(screen.getByLabelText('URL Link'), 'https://example.com/timetable.xml');
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
};

const provideViaFile = async () => {
  await userEvent.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
  await userEvent.upload(screen.getByLabelText('Upload file'), xmlFile);
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
};

describe('Timetable - Publish - Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue({});
  });

  it('does not advance from description step until required fields are valid', async () => {
    render(<TimetablePublishPage />);

    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('heading', { name: 'Describe your data set' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Choose how to provide your data set' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'There is a problem' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Enter a description in the data set description box below' })).toHaveAttribute('href', '#id_description');
    expect(screen.getByRole('link', { name: 'Enter a short description in the data set short description box below' })).toHaveAttribute('href', '#id_short_description');
  });

  it('renders user guidance and routes cancellation to its confirmation page', async () => {
    render(<TimetablePublishPage />);

    expect(screen.getByText('This information will give context to data consumers. Please be descriptive, but do not use personally identifiable information.')).toBeInTheDocument();
    expect(screen.getByText('This info will be displayed on your published data set dashboard to identify this data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 characters.')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/new/cancel');
  });

  it('does not submit until the provide-data step is valid', async () => {
    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('link', { name: 'Select how you want to provide your data set' })).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('shows URL guidance in a conditional section when link upload is selected', async () => {
    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await userEvent.click(screen.getByLabelText('Provide a link to your data set'));

    expect(screen.getByText('Please provide data set URI that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files')).toBeInTheDocument();
    const urlInput = screen.getByLabelText('URL Link');
    expect(urlInput).toHaveClass('govuk-!-width-three-quarters');
    expect(urlInput.closest('.govuk-radios__conditional')).not.toBeNull();
  });

  it('shows file guidance and confirmation in a conditional section when a file is selected', async () => {
    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await userEvent.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));

    const fileInput = screen.getByLabelText('Upload file');
    expect(screen.getByText('Please provide data set file that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files')).toBeInTheDocument();
    expect(fileInput.closest('.govuk-radios__conditional')).not.toBeNull();
    expect(fileInput).toHaveClass('govuk-!-width-three-quarters');

    await userEvent.upload(fileInput, xmlFile);

    expect(screen.getByText('Your file has been selected').closest('.govuk-radios__conditional')).toBeNull();
  });

  it('shows an error summary and allows cancellation from the provide-data step', async () => {
    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('heading', { name: 'There is a problem' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Select how you want to provide your data set' })).toHaveAttribute('href', '#method-link');

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/new/cancel?step=provide-data');
  });

  it.each([
    {
      name: 'posts link data and redirects to validation from the API response',
      provideData: provideViaLink,
      apiResponse: { redirect: '/publish/org/123/dataset/timetable/456/review' },
      expectedSelectedItem: 'url_link-conditional',
      expectedPayload: { url_link: 'https://example.com/timetable.xml' },
      expectedRedirect: '/publish/org/123/dataset/timetable/456/review',
    },
    {
      name: 'posts file data and routes to success when the API does not provide a redirect',
      provideData: provideViaFile,
      apiResponse: {},
      expectedSelectedItem: 'upload_file-conditional',
      expectedPayload: { upload_file: xmlFile },
      expectedRedirect: '/publish/org/123/dataset/timetable/new/success',
    },
  ])('$name', async ({ provideData, apiResponse, expectedSelectedItem, expectedPayload, expectedRedirect }) => {
    (api.post as jest.Mock).mockResolvedValue(apiResponse);

    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await provideData();

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const submittedFormData = (api.post as jest.Mock).mock.calls[0][1] as FormData;

    expect(api.post).toHaveBeenCalledWith('/api/publish/timetables/create/123/', expect.any(FormData));
    expect(submittedFormData.get('description')).toBe('A useful timetable');
    expect(submittedFormData.get('short_description')).toBe('Timetable');
    expect(submittedFormData.get('selected_item')).toBe(expectedSelectedItem);
    Object.entries(expectedPayload).forEach(([key, value]) => {
      expect(submittedFormData.get(key)).toBe(value);
    });
    expect(mockPush).toHaveBeenCalledWith(expectedRedirect);
  });
});