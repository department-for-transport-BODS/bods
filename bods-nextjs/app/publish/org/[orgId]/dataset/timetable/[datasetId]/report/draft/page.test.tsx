import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableDataQualityReportPage from './page';
import { api } from '@/lib/api-client';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '12', datasetId: '34' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

const report = {
  reportId: 56,
  title: 'My timetable',
  busServicesAffected: 1,
  hasCriticalIssues: true,
  levels: [
    {
      level: 'Critical',
      count: 2,
      intro: 'Critical intro',
      categories: [
        {
          category: 'Journeys',
          count: 2,
          suppressedCount: 0,
          observations: [
            { observation: 'Missing journey code', slug: 'missing-journey-code', count: 2, suppressedCount: 0 },
          ],
        },
      ],
    },
    {
      level: 'Advisory',
      count: 1,
      intro: 'Advisory intro',
      categories: [
        {
          category: 'Stops',
          count: 1,
          suppressedCount: 3,
          observations: [{ observation: 'Incorrect stop type', slug: null, count: 1, suppressedCount: 3 }],
        },
      ],
    },
  ],
};

describe('Timetable data quality report page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.history.replaceState(null, '', '/');
  });

  it('selects the linked tab and follows hash changes', async () => {
    window.history.replaceState(null, '', '/#Advisory');
    mockGet.mockResolvedValue(report);
    render(<TimetableDataQualityReportPage />);

    const advisory = await screen.findByRole('tab', { name: 'Advisory' });
    expect(advisory).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { name: 'Advisory observations (1)' })).toBeInTheDocument();

    act(() => {
      window.history.replaceState(null, '', '/#Critical');
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });
    expect(screen.getByRole('tab', { name: 'Critical' })).toHaveAttribute('aria-selected', 'true');
  });

  it('moves tab focus and selection with arrow keys and updates the hash', async () => {
    mockGet.mockResolvedValue(report);
    render(<TimetableDataQualityReportPage />);
    const critical = await screen.findByRole('tab', { name: 'Critical' });
    const advisory = screen.getByRole('tab', { name: 'Advisory' });
    const user = userEvent.setup();
    critical.focus();

    await user.keyboard('{ArrowRight}');
    expect(advisory).toHaveFocus();
    expect(advisory).toHaveAttribute('aria-selected', 'true');
    expect(critical).toHaveAttribute('tabindex', '-1');
    expect(window.location.hash).toBe('#Advisory');

    await user.keyboard('{ArrowRight}');
    expect(critical).toHaveFocus();
    expect(critical).toHaveAttribute('aria-selected', 'true');
    await user.click(advisory);
    expect(window.location.hash).toBe('#Advisory');
  });

  it('renders the report overview with a CSV download link', async () => {
    mockGet.mockResolvedValue(report);

    render(<TimetableDataQualityReportPage />);

    expect(await screen.findByRole('heading', { name: 'Data quality report', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/timetables/data-quality-report/12/34/');
    expect(document.title).toBe('Data quality report');
    expect(screen.getByText('CRITICAL ISSUES')).toHaveClass('govuk-tag--red');
    expect(screen.getByRole('heading', { name: 'My timetable' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download data quality report.csv' })).toHaveAttribute(
      'href',
      '/api/publish/timetables/data-quality-report/12/34/56/csv/',
    );
    expect(screen.getByText('Critical observations')).toBeInTheDocument();
    expect(screen.getByText('Advisory observation')).toBeInTheDocument();

    const criticalPanel = screen.getByRole('tabpanel');
    expect(within(criticalPanel).getByRole('heading', { name: 'Critical observations (2)' })).toBeInTheDocument();
    expect(within(criticalPanel).getByRole('table', { name: 'Journeys (2)' })).toBeInTheDocument();
    expect(within(criticalPanel).queryByText(/suppressed/)).not.toBeInTheDocument();
    expect(within(criticalPanel).getByRole('link', { name: 'Missing journey code' })).toHaveAttribute(
      'href',
      '/publish/org/12/dataset/timetable/34/report/56/missing-journey-code',
    );
    expect(screen.getByRole('link', { name: 'What are the different type of observations?' })).toHaveAttribute(
      'href',
      expect.stringContaining('/guidance/data-quality-definitions'),
    );
  });

  it('switches tabs to show advisory observations with suppressed counts', async () => {
    mockGet.mockResolvedValue(report);
    render(<TimetableDataQualityReportPage />);

    await userEvent.click(await screen.findByRole('tab', { name: 'Advisory' }));

    const advisoryPanel = screen.getByRole('tabpanel');
    expect(within(advisoryPanel).getByRole('heading', { name: 'Advisory observations (1)' })).toBeInTheDocument();
    expect(within(advisoryPanel).getByRole('columnheader', { name: 'Number of suppressed observations' })).toBeInTheDocument();
    expect(within(advisoryPanel).getByRole('row', { name: '1 3 Incorrect stop type' })).toBeInTheDocument();
  });

  it('shows an error when the report cannot be loaded', async () => {
    mockGet.mockRejectedValue(new Error('not found'));

    render(<TimetableDataQualityReportPage />);

    expect(
      await screen.findByText('Unable to load the data quality report. Please refresh and try again.'),
    ).toBeInTheDocument();
  });
});
