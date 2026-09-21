import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableUpdatePage from './page';
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

describe('TimetableUpdatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue({
      redirect: '/publish/org/123/dataset/timetable/456/review',
    });
  });

  it('replaces the draft file and returns to validation review', async () => {
    render(<TimetableUpdatePage />);
    const user = userEvent.setup();
    const file = new File(['<xml />'], 'replacement.xml', { type: 'text/xml' });

    await user.click(screen.getByLabelText('Upload data set to Bus Open Data Service'));
    await user.upload(screen.getByLabelText('Upload file'), file);
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const formData = (api.post as jest.Mock).mock.calls[0][1] as FormData;
    expect(api.post).toHaveBeenCalledWith('/api/publish/timetables/update/123/456/', expect.any(FormData));
    expect(formData.get('selected_item')).toBe('upload_file-conditional');
    expect(formData.get('upload_file')).toBe(file);
    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/timetable/456/review');
  });

  it('uses the provide-data stepper and links Cancel to its confirmation page', () => {
    render(<TimetableUpdatePage />);

    expect(screen.getByText('1. Describe data')).toBeInTheDocument();
    expect(screen.getByText('2. Provide data')).toBeInTheDocument();
    expect(screen.getByText('3. Review and publish')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/456/update/cancel',
    );
  });
});
