import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableReviewUpdatePage from './page';
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

describe('TimetableReviewUpdatePage (Django TimetableUploadModify)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockResolvedValue({ urlLink: 'https://example.com/draft.xml' });
    (api.post as jest.Mock).mockResolvedValue({ redirect: '/publish/org/123/dataset/timetable/456/review' });
  });

  it('matches the Django title, heading and Describe / Provide stepper', async () => {
    render(<TimetableReviewUpdatePage />);

    expect(document.title).toBe('Provide data: upload');
    expect(screen.getByRole('group', { name: 'Choose how to provide your data set' })).toBeInTheDocument();
    expect(screen.getByText('1. Describe data')).toBeInTheDocument();
    expect(screen.getByText('2. Provide data').closest('li')).toHaveClass('publish-stepper__item--selected');
    expect(screen.queryByText('1. Comment')).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText('URL Link')).toHaveValue('https://example.com/draft.xml'));
    expect(api.get).toHaveBeenCalledWith('/api/publish/timetables/review-status/123/456/');
  });

  it('replaces the draft data and returns to review', async () => {
    render(<TimetableReviewUpdatePage />);
    const user = userEvent.setup();
    const file = new File(['<xml />'], 'replacement.xml', { type: 'text/xml' });

    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload File'), file);
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const formData = (api.post as jest.Mock).mock.calls[0][1] as FormData;
    expect(formData.get('modify_draft')).toBe('true');
    expect(formData.get('is_update')).toBeNull();
    expect(formData.get('comment')).toBeNull();
    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/review');
  });

  it('confirms cancelling back to review', async () => {
    render(<TimetableReviewUpdatePage />);

    await userEvent.setup().click(screen.getByRole('button', { name: 'Cancel' }));

    expect(document.title).toBe('Provide data: cancel');
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      publishPath('/org/123/dataset/timetable/456/review/'),
    );
  });
});
