import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetablePublishPage from './page';
import { api } from '@/lib/api-client';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useRouter: () => ({ push: mockPush }),
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
  await userEvent.type(screen.getByLabelText('Dataset short description'), 'Timetable');
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
};

const xmlFile = new File(['<xml />'], 'timetable.xml', { type: 'text/xml' });

const provideViaLink = async () => {
  await userEvent.click(screen.getByLabelText('Provide a link to your data set'));
  await userEvent.type(screen.getByLabelText('URL link'), 'https://example.com/timetable.xml');
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
};

const provideViaFile = async () => {
  await userEvent.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
  await userEvent.upload(screen.getByLabelText('Upload file'), xmlFile);
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
};

const giveConsentAndPublish = async () => {
  await userEvent.click(
    screen.getByLabelText('I have reviewed the data quality report and wish to publish my data'),
  );
  await userEvent.click(screen.getByRole('button', { name: 'Publish' }));
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
  });

  it('does not submit until the data quality confirmation is checked', async () => {
    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await provideViaLink();
    await userEvent.click(screen.getByRole('button', { name: 'Publish' }));

    expect(
      screen.getByText('You must confirm you have reviewed the data quality report before publishing'),
    ).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it.each([
    {
      name: 'posts link data and follows an internal redirect from the API response',
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
      expectedRedirect: '/publish/org/123/dataset/timetable/create/success',
    },
  ])('$name', async ({ provideData, apiResponse, expectedSelectedItem, expectedPayload, expectedRedirect }) => {
    (api.post as jest.Mock).mockResolvedValue(apiResponse);

    render(<TimetablePublishPage />);

    await fillDescriptionStep();
    await provideData();
    await giveConsentAndPublish();

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