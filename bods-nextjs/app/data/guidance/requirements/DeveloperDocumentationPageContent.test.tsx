import { render, screen, within } from '@testing-library/react';
import { usePathname, useSearchParams } from 'next/navigation';
import DeveloperDocumentationPageContent from './DeveloperDocumentationPageContent';

jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
  useSearchParams: jest.fn(),
}));

jest.mock('./sections', () => ({
  ApiReferenceSection: () => <div>API reference section</div>,
  BrowseDataSection: () => <div>Browse data section</div>,
  CaseStudiesSection: () => <div>Case studies section</div>,
  DataByOperatorSection: () => <div>Data by operator section</div>,
  DataCatalogueSection: () => <div>Data catalogue section</div>,
  DataFormatsSection: () => <div>Data formats section</div>,
  DownloadingDataSection: () => <div>Downloading data section</div>,
  HelpSection: () => <div>Help section</div>,
  MaintainingQualityDataSection: () => <div>Maintaining quality data section</div>,
  OverviewSection: () => <div>Overview section</div>,
  QuickStartSection: () => <div>Quick start section</div>,
  UsingApiSection: () => <div>Using API section</div>,
}));

const PATHNAME = '/data/guidance/requirements';

function renderWithSection(section?: string) {
  const params = new URLSearchParams(section ? { section } : {});
  (usePathname as jest.Mock).mockReturnValue(PATHNAME);
  (useSearchParams as jest.Mock).mockReturnValue(params);
  return render(<DeveloperDocumentationPageContent />);
}

describe('DeveloperDocumentationPageContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the overview section by default', () => {
    renderWithSection();

    expect(screen.getByRole('heading', { name: 'Developer documentation' })).toBeInTheDocument();
    expect(screen.getByText('Overview section')).toBeInTheDocument();
  });

  it('renders the section requested by the query param', () => {
    renderWithSection('dataformats');

    expect(screen.getByText('Data formats section')).toBeInTheDocument();
    expect(screen.queryByText('Overview section')).not.toBeInTheDocument();
  });

  it('falls back to the overview section for an unknown query param', () => {
    renderWithSection('does-not-exist');

    expect(screen.getByText('Overview section')).toBeInTheDocument();
  });

  it('builds contents links with the pathname so the section query param is preserved', () => {
    renderWithSection('browse');

    expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', `${PATHNAME}?section=overview`);
    expect(screen.getByRole('link', { name: 'API reference' })).toHaveAttribute(
      'href',
      `${PATHNAME}?section=apireference`,
    );
  });

  it('marks the current section link as active', () => {
    renderWithSection('casestudies');

    const activeLink = screen.getByRole('link', { name: 'Case studies' });
    expect(activeLink).toHaveClass('link-dark');
    expect(activeLink).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'Overview' })).not.toHaveClass('link-dark');
  });

  it('renders previous and next pagination links with the pathname', () => {
    renderWithSection('download');

    const prev = within(screen.getByRole('navigation', { name: 'Pagination Prev' })).getByRole('link');
    const next = within(screen.getByRole('navigation', { name: 'Pagination Next' })).getByRole('link');

    expect(prev).toHaveAttribute('href', `${PATHNAME}?section=browse`);
    expect(next).toHaveAttribute('href', `${PATHNAME}?section=api`);
  });

  it('hides the previous link on the first section', () => {
    renderWithSection('overview');

    expect(screen.queryByRole('navigation', { name: 'Pagination Prev' })).not.toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Pagination Next' })).toBeInTheDocument();
  });

  it('hides the next link on the last section', () => {
    renderWithSection('help');

    expect(screen.getByRole('navigation', { name: 'Pagination Prev' })).toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: 'Pagination Next' })).not.toBeInTheDocument();
  });
});
