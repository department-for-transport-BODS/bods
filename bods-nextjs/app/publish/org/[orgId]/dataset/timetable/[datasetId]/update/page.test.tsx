import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableUpdatePage from './page';
import { ApiError, api } from '@/lib/api-client';
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
  ...jest.requireActual('@/lib/api-client'),
  api: { post: jest.fn(), get: jest.fn() },
}));

const continueToUpload = async (user: ReturnType<typeof userEvent.setup>, comment = 'New stops') => {
  await user.type(screen.getByLabelText('Comment on data set updates'), comment);
  await user.click(screen.getByRole('button', { name: 'Continue' }));
};

describe('TimetableUpdatePage (Django FeedUpdateWizard)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockResolvedValue({ urlLink: 'https://example.com/live.xml' });
    (api.post as jest.Mock).mockResolvedValue({
      redirect: '/publish/org/123/dataset/timetable/456/update/review',
    });
  });

  it('starts on the comment step with the Comment / Update stepper', () => {
    render(<TimetableUpdatePage />);

    expect(document.title).toBe('Update data set: comment');
    expect(
      screen.getByRole('heading', { level: 1, name: 'Provide a comment on what has been updated' }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Comment on data set updates')).toHaveAttribute('name', 'comment-comment');
    expect(screen.getByText('1. Comment').closest('li')).toHaveClass('publish-stepper__item--selected');
    expect(screen.getByText('2. Update')).toBeInTheDocument();
  });

  it('requires a comment with the Django message', async () => {
    render(<TimetableUpdatePage />);

    await userEvent.setup().click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('link', { name: 'Enter a comment in the box below' })).toHaveAttribute(
      'href',
      '#id_comment-comment',
    );
    expect(document.title).toBe('Error: Update data set: comment');
  });

  it('pre-fills the URL link from the live revision on the upload step', async () => {
    render(<TimetableUpdatePage />);
    const user = userEvent.setup();

    await continueToUpload(user);

    expect(api.get).toHaveBeenCalledWith('/api/publish/timetables/update/123/456/');
    expect(document.title).toBe('Update data set: upload');
    expect(screen.getByRole('group', { name: 'Update your published data set' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText('URL Link')).toHaveValue('https://example.com/live.xml'));
  });

  it('posts the comment and data to start a draft, then goes to update/review', async () => {
    render(<TimetableUpdatePage />);
    const user = userEvent.setup();
    const file = new File(['<xml />'], 'replacement.xml', { type: 'text/xml' });

    await continueToUpload(user);
    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload File'), file);
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const formData = (api.post as jest.Mock).mock.calls[0][1] as FormData;
    expect(api.post).toHaveBeenCalledWith('/api/publish/timetables/update/123/456/', expect.any(FormData));
    expect(formData.get('comment')).toBe('New stops');
    expect(formData.get('upload_file')).toBe(file);
    expect(formData.get('modify_draft')).toBeNull();
    expect(formData.get('is_update')).toBeNull();
    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/update/review');
  });

  it('returns to the comment step when the server rejects the comment', async () => {
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('Invalid', 400, { comment: ['This comment has already been used'] }),
    );
    render(<TimetableUpdatePage />);
    const user = userEvent.setup();

    await continueToUpload(user);
    await user.click(screen.getByLabelText('Provide a link to your data set'));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    expect(
      await screen.findByRole('link', { name: 'This comment has already been used' }),
    ).toHaveAttribute('href', '#id_comment-comment');
    expect(screen.getByLabelText('Comment on data set updates')).toHaveValue('New stops');
  });

  it('confirms cancelling back to the data set page', async () => {
    render(<TimetableUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(document.title).toBe('Update data set: cancel');
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      publishPath('/org/123/dataset/timetable/456/'),
    );
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByLabelText('Comment on data set updates')).toBeInTheDocument();
  });
});
