import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import { publishPath } from '@/config/client';
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

const successStatus = {
  datasetId: 9,
  revisionId: 42,
  status: 'success',
  progress: 100,
  loading: false,
  name: 'Draft timetable',
  description: 'A description',
  shortDescription: 'Short',
  ownerName: 'Test Org',
  downloadUrl: 'https://example.com/feed.xml',
  publisherUrl: 'https://example.com/feed.xml',
  transxchangeVersion: '2.4',
  lastModified: '2026-11-02T12:44:00Z',
  lastModifiedUser: null,
  error: null,
  validationState: 'passed',
  distinctAttributes: {},
  dataQuality: { status: 'PENDING' },
};

describe('TimetableReviewPageContent', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('processed draft', () => {
    it('renders the Django property table with revision-edit links and Last updated', () => {
      renderContent(successStatus, true);

      const rowHeaders = screen.getAllByRole('rowheader').map((cell) => cell.textContent);
      expect(rowHeaders).toEqual([
        'Name',
        'Description',
        'Short description',
        'Status',
        'Data quality report',
        'Owner',
        'TransXChange version',
        'URL link',
        'Last updated',
      ]);
      screen.getAllByRole('link', { name: 'Edit' }).forEach((link) =>
        expect(link).toHaveAttribute('href', publishPath('/org/1/dataset/timetable/9/revision-edit/')),
      );
      expect(screen.getByText(/by System/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Delete data' })).toHaveAttribute(
        'href',
        publishPath('/org/1/dataset/timetable/9/delete/'),
      );
    });

    it('hides the consent form while the data quality report is generating', () => {
      renderContent(successStatus);

      expect(screen.getByText('Generating...')).toBeInTheDocument();
      expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    });

    it('shows the Django consent form once the data quality report is ready', () => {
      renderContent({ ...successStatus, dataQuality: { status: 'SUCCESS', reportId: 5, hasCriticalIssues: false, showUpdate: true } });

      const consent = screen.getByLabelText('I have reviewed the data quality report and wish to publish my data');
      expect(consent).toHaveAttribute('name', 'consent');
      expect(consent).toHaveAttribute('id', 'id_consent');
      expect(screen.getByRole('button', { name: 'Publish data' })).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Update data' })).toHaveAttribute(
        'href',
        publishPath('/org/1/dataset/timetable/9/review/update'),
      );
    });
  });

  describe('first publish (review/)', () => {
    it('uses the Describe data / Provide data stepper', () => {
      renderContent({ ...failedStatus, loading: true });

      expect(screen.getByText('1. Describe data')).toBeInTheDocument();
      expect(screen.getByText('2. Provide data')).toBeInTheDocument();
      expect(screen.queryByText('1. Comment')).not.toBeInTheDocument();
    });

    it('links the failed upload to review/update', () => {
      renderContent(failedStatus);

      expect(screen.getByRole('button', { name: 'Publish correct data set' })).toHaveAttribute(
        'href',
        publishPath('/org/1/dataset/timetable/9/review/update'),
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

      expect(screen.getByRole('button', { name: 'Publish correct data set' })).toHaveAttribute(
        'href',
        publishPath('/org/1/dataset/timetable/9/update/review/update'),
      );
    });
  });
});

describe('getTimetablePublishRedirect', () => {
  const ids = { orgId: '1', datasetId: '9' };

  it('goes to update/success after publishing an update revision', () => {
    expect(getTimetablePublishRedirect({ ...ids, isUpdate: true })).toBe(
      publishPath('/org/1/dataset/timetable/9/update/success'),
    );
  });

  it('goes to success after a first publish, like Django PublishRevisionView', () => {
    expect(getTimetablePublishRedirect({ ...ids, isUpdate: false })).toBe(
      publishPath('/org/1/dataset/timetable/9/success'),
    );
  });
});
