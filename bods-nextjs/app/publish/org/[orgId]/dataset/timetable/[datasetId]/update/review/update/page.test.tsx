import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableUpdateReviewUpdatePage from './page';
import { api } from '@/lib/api-client';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123', datasetId: '456' }),
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: jest.fn() },
}));

describe('TimetableUpdateReviewUpdatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue({
      redirect: '/publish/org/123/dataset/timetable/456/update/review',
    });
  });

  it('matches Django DatasetUpdateModify: title, heading and Comment/Update stepper', () => {
    render(<TimetableUpdateReviewUpdatePage />);

    expect(document.title).toBe('Update data set: upload');
    expect(screen.getByRole('heading', { level: 1, name: 'Choose how to provide your data set' })).toBeInTheDocument();
    expect(screen.getByText('1. Comment')).toBeInTheDocument();
    expect(screen.getByText('2. Update').closest('li')).toHaveClass('publish-stepper__item--selected');
    expect(screen.getByText('3. Review and publish')).toBeInTheDocument();
  });

  it('links Cancel to the update/review/update confirmation page', () => {
    render(<TimetableUpdateReviewUpdatePage />);

    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/456/update/review/update/cancel',
    );
  });

  it('posts is_update and returns to update/review', async () => {
    render(<TimetableUpdateReviewUpdatePage />);
    const user = userEvent.setup();
    const file = new File(['<xml />'], 'replacement.xml', { type: 'text/xml' });

    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload file'), file);
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const formData = (api.post as jest.Mock).mock.calls[0][1] as FormData;
    expect(api.post).toHaveBeenCalledWith('/api/publish/timetables/update/123/456/', expect.any(FormData));
    expect(formData.get('is_update')).toBe('true');
    expect(formData.get('upload_file')).toBe(file);
    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/update/review');
  });

  it('falls back to update/review when the API returns no redirect', async () => {
    (api.post as jest.Mock).mockResolvedValue({});
    render(<TimetableUpdateReviewUpdatePage />);
    const user = userEvent.setup();

    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload file'), new File(['<xml />'], 'a.xml', { type: 'text/xml' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/update/review'),
    );
  });
});
