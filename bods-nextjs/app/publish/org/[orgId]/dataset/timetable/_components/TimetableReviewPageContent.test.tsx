import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import { getTimetablePublishRedirect, TimetableReviewPageContent } from './TimetableReviewPageContent';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
}));

jest.mock('@/hooks/useDatasetReview', () => ({
  useDatasetReview: jest.fn(),
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

jest.mock('@/components/data/MapboxRouteMap', () => ({
  MapboxRouteMap: () => <div data-testid="route-map" />,
}));

const mockUseDatasetReview = useDatasetReview as jest.Mock;

const renderContent = (status: Record<string, unknown> | null, isUpdate?: boolean) => {
  mockUseDatasetReview.mockReturnValue({
    statusData: status,
    progress: 50,
    isInitialLoading: false,
    errorMessage: '',
    setErrorMessage: jest.fn(),
  });
  return render(<TimetableReviewPageContent isUpdate={isUpdate} />);
};

const failedStatus = {
  datasetId: 9,
  revisionId: 42,
  status: 'error',
  progress: 100,
  loading: false,
  name: 'Timetable data set',
  ownerName: 'Test Org',
  error: 'SCHEMA_ERROR',
  errorDescription: 'The file is not valid',
};

describe('TimetableReviewPageContent', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('first publish (review/)', () => {
    it('uses the Describe data / Provide data stepper', () => {
      renderContent({ ...failedStatus, loading: true });

      expect(screen.getByText('1. Describe data')).toBeInTheDocument();
      expect(screen.getByText('2. Provide data')).toBeInTheDocument();
      expect(screen.queryByText('1. Comment')).not.toBeInTheDocument();
    });

    it('links the failed upload back to the update page', () => {
      renderContent(failedStatus);

      expect(screen.getByRole('link', { name: 'Publish correct data set' })).toHaveAttribute(
        'href',
        '/publish/org/1/dataset/timetable/9/update',
      );
    });
  });

  describe('update revision (update/review/)', () => {
    it('uses the Comment / Update stepper', () => {
      renderContent({ ...failedStatus, loading: true }, true);

      expect(screen.getByText('1. Comment')).toBeInTheDocument();
      expect(screen.getByText('2. Update')).toBeInTheDocument();
      expect(screen.getByText('3. Review and publish')).toBeInTheDocument();
      expect(screen.queryByText('1. Describe data')).not.toBeInTheDocument();
    });

    it('selects the Update step while the data is validating', () => {
      renderContent({ ...failedStatus, loading: true }, true);

      expect(screen.getByText('2. Update').closest('li')).toHaveClass(
        'publish-stepper__item--selected',
      );
    });

    it('links the failed upload to update/review/update', () => {
      renderContent(failedStatus, true);

      expect(screen.getByRole('link', { name: 'Publish correct data set' })).toHaveAttribute(
        'href',
        '/publish/org/1/dataset/timetable/9/update/review/update',
      );
    });
  });
});

describe('getTimetablePublishRedirect', () => {
  const ids = { orgId: '1', datasetId: '9' };

  it('goes to update/success after publishing an update revision', () => {
    expect(getTimetablePublishRedirect({ ...ids, isUpdate: true }, '/publish/org/1/dataset/timetable')).toBe(
      '/publish/org/1/dataset/timetable/9/update/success',
    );
  });

  it('follows the server redirect for a first publish', () => {
    expect(getTimetablePublishRedirect({ ...ids, isUpdate: false }, '/somewhere')).toBe('/somewhere');
  });

  it('falls back to the timetable list for a first publish', () => {
    expect(getTimetablePublishRedirect({ ...ids, isUpdate: false })).toBe('/publish/org/1/dataset/timetable');
  });
});
