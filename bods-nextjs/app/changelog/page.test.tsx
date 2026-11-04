import { render, screen, within } from '@testing-library/react';
import ChangelogPage from './page';
import { getKnownIssues, type KnownIssues } from '@/lib/changelog/known-issues';
import { getReleaseNotes } from '@/lib/changelog/release-notes';
import { dataPath, publishAppPath, wwwPath } from '@/config/client';

jest.mock('next/server', () => ({
  connection: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@/lib/changelog/known-issues', () => ({
  getKnownIssues: jest.fn(),
}));

jest.mock('@/lib/changelog/release-notes', () => ({
  getReleaseNotes: jest.fn(),
}));

const noIssues: KnownIssues = { publisher: [], consumer: [] };

async function renderPage(knownIssues: KnownIssues = noIssues) {
  (getKnownIssues as jest.Mock).mockResolvedValue(knownIssues);
  render(await ChangelogPage());
}

describe('ChangelogPage', () => {
  beforeEach(() => {
    (getReleaseNotes as jest.Mock).mockResolvedValue([
      {
        version: '1.60.0',
        date: '2026-06',
        summary: 'This release deployed the following changes:',
        items: ['Optimised queries.', 'Use the `Service > OperatingPeriod` element.'],
      },
      { version: '1.24.0', date: '2023-03', summary: 'Fares report updates.', items: [] },
    ]);
  });

  it('renders the "Need further guidance?" links', async () => {
    await renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Service changelog' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Service Changelog' })).toHaveAttribute(
      'href',
      wwwPath('/changelog/'),
    );
    expect(screen.getByRole('link', { name: 'View operator guidance' })).toHaveAttribute(
      'href',
      publishAppPath('/guidance/operator-requirements/'),
    );
    expect(screen.getByRole('link', { name: 'View developer guidance' })).toHaveAttribute(
      'href',
      dataPath('/guidance/requirements/'),
    );
    expect(screen.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute(
      'href',
      wwwPath('/contact/'),
    );
  });

  it('renders release notes from the loader', async () => {
    await renderPage();

    expect(screen.getByRole('heading', { level: 3, name: 'June 2026 (1.60.0)' })).toHaveClass(
      'govuk-heading-m',
      'govuk-!-margin-bottom-5',
    );
    expect(screen.getByRole('heading', { level: 4, name: 'Release 1.60.0 (June 2026)' })).toHaveClass(
      'govuk-heading-s',
      'govuk-!-margin-bottom-5',
    );
    expect(screen.getByRole('heading', { level: 3, name: 'March 2023 (1.24.0)' })).toBeInTheDocument();
    expect(screen.getByText('Optimised queries.')).toBeInTheDocument();
    expect(screen.getByText('Service > OperatingPeriod').tagName).toBe('CODE');
    expect(screen.getByText('Fares report updates.')).toBeInTheDocument();
  });

  it('hides the known issues block when there are no issues', async () => {
    await renderPage();

    expect(screen.queryByRole('heading', { name: 'Known Issues' })).not.toBeInTheDocument();
  });

  it('shows only non-empty issue sections and tags fixed issues', async () => {
    await renderPage({
      publisher: [
        { description: 'Upload is slow', status: 'fixed', modified: '2026-06-02T10:00:00Z' },
        { description: 'Report missing', status: 'pending', modified: '2026-06-01T10:00:00Z' },
      ],
      consumer: [],
    });

    expect(screen.getByRole('heading', { name: 'Known Issues' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Publisher issues:' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Consumer issues:' })).not.toBeInTheDocument();

    const [fixedIssue, pendingIssue] = screen
      .getAllByRole('listitem')
      .filter((item) => /Upload is slow|Report missing/.test(item.textContent ?? ''));
    expect(within(fixedIssue).getByText('Fixed')).toHaveClass('govuk-tag', 'govuk-tag--green');
    expect(within(pendingIssue).queryByText('Fixed')).not.toBeInTheDocument();
  });
});
