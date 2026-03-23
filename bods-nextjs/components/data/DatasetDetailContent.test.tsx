/**
 * Dataset Detail Content Component Tests
 * 
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DatasetDetailContent } from './DatasetDetailContent';
import type { Dataset } from '@/types';

const mockRouteMap = jest.fn(() => <div data-testid="route-map" />);

jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

jest.mock('./RouteMap', () => ({
  RouteMap: (props: unknown) => mockRouteMap(props),
}));

const mockDataset: Dataset = {
  id: 123,
  organisationId: 456,
  revisionId: 789,
  created: '2024-01-01T10:00:00Z',
  modified: '2024-01-15T14:30:00Z',
  operatorName: 'Test Operator Ltd',
  noc: ['TEST'],
  name: 'Test Bus Service Dataset',
  description: 'A comprehensive dataset for test bus services',
  comment: '',
  status: 'published',
  url: 'https://example.com/dataset/123/download',
  extension: 'xml',
  lines: ['1', '2', '3', '4', '5'],
  firstStartDate: '2024-01-01T00:00:00Z',
  firstEndDate: '2024-12-31T23:59:59Z',
  lastEndDate: '2024-12-31T23:59:59Z',
  adminAreas: [
    { atco_code: '110', name: 'London' },
    { atco_code: '120', name: 'Manchester' },
  ],
  localities: [
    { gazetteer_id: 'E0123456', name: 'Westminster' },
  ],
  dqScore: '85.5%',
  dqRag: 'green',
  bodsCompliance: true,
};

describe('DatasetDetailContent', () => {
  beforeEach(() => {
    mockRouteMap.mockClear();
  });

  it('renders dataset name and ID', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText('Test Bus Service Dataset')).toBeInTheDocument();
    expect(screen.getByText('123')).toBeInTheDocument();
  });

  it('renders dataset description', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText('A comprehensive dataset for test bus services')).toBeInTheDocument();
  });

  it('renders operator name with link', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    const operatorLink = screen.getByRole('link', { name: /Test Operator Ltd/i });
    expect(operatorLink).toBeInTheDocument();
    expect(operatorLink).toHaveAttribute('href', '/data?organisation=456&status=live');
  });

  it('renders status badge correctly', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    const statusBadge = screen.getByText('Published');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge).toHaveClass('govuk-tag--green');
  });

  it('renders data quality score and RAG', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByLabelText('Data quality score: 85.5%, rated GREEN')).toBeInTheDocument();
  });

  it('renders formatted last updated date', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText(/15 Jan 2024 14:30/i)).toBeInTheDocument();
  });

  it('renders geographic coverage', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText('Geographic coverage')).toBeInTheDocument();
    expect(screen.getByText('London')).toBeInTheDocument();
    expect(screen.getByText('Manchester')).toBeInTheDocument();
  });

  it('renders line information', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText(/This dataset contains 5 lines/i)).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('renders API URL', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByRole('heading', { name: /Use this data set in your code/i })).toBeInTheDocument();
    expect(screen.getByText('https://example.com/dataset/123/download')).toBeInTheDocument();
  });

  it('renders download button with correct URL', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    const downloadButton = screen.getByRole('link', { name: /Download dataset/i });
    expect(downloadButton).toBeInTheDocument();
    expect(downloadButton).toHaveAttribute('href', mockDataset.url);
  });

  it('toggles subscription state', async () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    const subscribeButton = screen.getByRole('button', { name: /Subscribe to this data set/i });
    expect(subscribeButton).toBeInTheDocument();

    fireEvent.click(subscribeButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Unsubscribe from this data set/i })).toBeInTheDocument();
    });
  });

  it('handles missing description gracefully', () => {
    const datasetWithoutDescription = {
      ...mockDataset,
      description: '',
    };

    render(<DatasetDetailContent dataset={datasetWithoutDescription} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText('No description provided')).toBeInTheDocument();
  });

  it('handles unavailable data quality', () => {
    const datasetWithNoDQ = {
      ...mockDataset,
      dqRag: 'unavailable' as const,
      dqScore: '0%',
    };

    render(<DatasetDetailContent dataset={datasetWithNoDQ} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.queryByText(/Data quality report/i)).not.toBeInTheDocument();
  });

  it('renders change log link', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    const changeLogLink = screen.getByRole('link', { name: /View change log/i });
    expect(changeLogLink).toBeInTheDocument();
    expect(changeLogLink).toHaveAttribute('href', `/data/${mockDataset.id}/changelog`);
  });

  it('passes the live revision ID to the route map', () => {
    render(<DatasetDetailContent dataset={mockDataset} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(mockRouteMap).toHaveBeenCalledWith(
      expect.objectContaining({
        revisionId: mockDataset.revisionId,
      })
    );
  });

  it('truncates long line lists', () => {
    const datasetWithManyLines = {
      ...mockDataset,
      lines: Array.from({ length: 25 }, (_, i) => `Line ${i + 1}`),
    };

    render(<DatasetDetailContent dataset={datasetWithManyLines} formattedLastUpdated="15 Jan 2024 14:30" />);

    expect(screen.getByText(/This dataset contains 25 lines/i)).toBeInTheDocument();
    expect(screen.getByText(/...and 15 more/i)).toBeInTheDocument();
  });
});
