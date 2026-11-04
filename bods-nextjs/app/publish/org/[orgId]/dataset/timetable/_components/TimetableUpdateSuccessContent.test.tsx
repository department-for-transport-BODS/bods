import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { api } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';
import { TimetableUpdateSuccessContent } from './TimetableUpdateSuccessContent';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

describe('TimetableUpdateSuccessContent', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows the first-publish confirmation', async () => {
    mockGet.mockResolvedValue({ isPtiCompliant: true, ptiEnforcedDate: '2021-08-02' });

    render(<TimetableUpdateSuccessContent />);

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Your data set has been successfully published' }),
    ).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/timetables/update-success/1/9/');
    expect(document.title).toBe('Data set published');
  });

  it('shows the PTI compliant confirmation', async () => {
    mockGet.mockResolvedValue({ isPtiCompliant: true, ptiEnforcedDate: '2021-08-02' });

    render(<TimetableUpdateSuccessContent update />);

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Your data set has been successfully updated' }),
    ).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/timetables/update-success/1/9/');
    expect(document.title).toBe('Data set updated');
    expect(screen.getByText('We have sent you a confirmation email.')).toBeInTheDocument();
    expect(screen.queryByText(/PTI profile/)).not.toBeInTheDocument();
  });

  it('warns about the PTI enforced date when the live data is not PTI compliant', async () => {
    mockGet.mockResolvedValue({ isPtiCompliant: false, ptiEnforcedDate: '2021-08-02' });

    render(<TimetableUpdateSuccessContent />);

    expect(
      await screen.findByText(
        "We have sent you a confirmation email. However please note that after 2nd August 2021, BODS won't be accepting any files which are not TransxChange PTI profile v1.1 compliant. Please contact your scheduling supplier to update your data.",
      ),
    ).toBeInTheDocument();
  });

  it('links to the data sets page and the published data set', async () => {
    mockGet.mockResolvedValue({ isPtiCompliant: true, ptiEnforcedDate: '2021-08-02' });

    render(<TimetableUpdateSuccessContent />);

    expect(await screen.findByRole('heading', { level: 2, name: 'What happens next?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'data sets page.' })).toHaveAttribute(
      'href',
      publishAppPath('/publish/org/1/dataset/timetable'),
    );
    expect(screen.getByRole('button', { name: 'View published data set' })).toHaveAttribute(
      'href',
      publishAppPath('/publish/org/1/dataset/timetable/9'),
    );
  });

  it('shows an error when the context cannot be loaded', async () => {
    mockGet.mockRejectedValue(new Error('Dataset not found'));

    render(<TimetableUpdateSuccessContent update />);

    expect(await screen.findByText('Dataset not found')).toBeInTheDocument();
    expect(screen.queryByText('Your data set has been successfully updated')).not.toBeInTheDocument();
  });
});
