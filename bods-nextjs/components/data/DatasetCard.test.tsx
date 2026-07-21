/**
 * DatasetCard Component Tests
 * 
 */

import { render, screen } from '@testing-library/react';
import { DatasetCard } from './DatasetCard';
import type { DatasetListItem } from '@/types';
import badgeStyles from './DataQualityBadge.module.css';

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('DatasetCard', () => {
  const mockDataset: DatasetListItem = {
    id: 123,
    name: 'Test Bus Routes Dataset',
    operatorName: 'Acme Bus Company',
    description: 'A comprehensive dataset of bus routes in the test region.',
    status: 'published',
    modified: '2026-01-15T10:30:00+00:00',
    dqScore: '85.5%',
    dqRag: 'green',
    dataType: 'TIMETABLE',
  };

  it('renders dataset name as a link', () => {
    render(<DatasetCard dataset={mockDataset} />);
    
    const link = screen.getByRole('link', { name: /view details for test bus routes dataset/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/data/123');
  });

  it('displays operator name', () => {
    render(<DatasetCard dataset={mockDataset} />);
    
    expect(screen.getByText('Acme Bus Company')).toBeInTheDocument();
  });

  it('displays formatted last updated date', () => {
    render(<DatasetCard dataset={mockDataset} />);
    
    expect(screen.getByText('15 January 2026')).toBeInTheDocument();
  });

  it('displays data quality score with green badge', () => {
    render(<DatasetCard dataset={mockDataset} />);

    const badge = screen.getByLabelText('Data quality score: 85.5%, rated GREEN');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('85.5% GREEN');
    expect(badge).toHaveClass(badgeStyles.statusIndicator, badgeStyles.success);
  });

  it('displays data type indicator', () => {
    render(<DatasetCard dataset={mockDataset} />);
    
    expect(screen.getByText('Timetable')).toBeInTheDocument();
  });

  it('displays description when provided', () => {
    render(<DatasetCard dataset={mockDataset} />);
    
    expect(screen.getByText(mockDataset.description)).toBeInTheDocument();
  });

  it('truncates long descriptions', () => {
    const longDescription = 'A'.repeat(200);
    const datasetWithLongDesc = { ...mockDataset, description: longDescription };
    
    render(<DatasetCard dataset={datasetWithLongDesc} />);
    
    const displayedText = screen.getByText(/^A+\.\.\.$/);
    expect(displayedText.textContent?.length).toBeLessThanOrEqual(153); // 150 + "..."
  });

  describe('data quality badge colors', () => {
    it.each([
      ['green', '85.5%', 'Data quality score: 85.5%, rated GREEN', badgeStyles.success],
      ['amber', '65.0%', 'Data quality score: 65.0%, rated AMBER', badgeStyles.warning],
      ['red', '30.0%', 'Data quality score: 30.0%, rated RED', badgeStyles.error],
    ] as const)('displays the expected badge for %s RAG status', (dqRag, dqScore, ariaLabel, expectedClass) => {
      const dataset = { ...mockDataset, dqRag, dqScore };
      render(<DatasetCard dataset={dataset} />);

      const badge = screen.getByLabelText(ariaLabel);
      expect(badge).toHaveTextContent(`${dqScore} ${dqRag.toUpperCase()}`);
      expect(badge).toHaveClass(badgeStyles.statusIndicator, expectedClass);
    });

    it('does not render a badge for unavailable RAG status', () => {
      const dataset = { ...mockDataset, dqRag: 'unavailable' as const };
      render(<DatasetCard dataset={dataset} />);

      expect(screen.queryByLabelText(/Data quality score:/i)).not.toBeInTheDocument();
    });
  });

  describe('data type badges', () => {
    it.each([
      ['TIMETABLE', 'Timetable', 'govuk-tag--blue'],
      ['AVL', 'Location', 'govuk-tag--purple'],
      ['FARES', 'Fares', 'govuk-tag--turquoise'],
    ] as const)('displays the expected badge for %s datasets', (dataType, label, expectedClass) => {
      const dataset = { ...mockDataset, dataType };
      render(<DatasetCard dataset={dataset} />);

      const badge = screen.getByText(label);
      expect(badge).toHaveClass(expectedClass);
    });
  });

  describe('accessibility', () => {
    it('has proper aria-label on dataset link', () => {
      render(<DatasetCard dataset={mockDataset} />);
      
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('aria-label', 'View details for Test Bus Routes Dataset');
    });

    it('has proper aria-label on quality badge', () => {
      render(<DatasetCard dataset={mockDataset} />);

      const badge = screen.getByLabelText('Data quality score: 85.5%, rated GREEN');
      expect(badge).toBeInTheDocument();
    });

    it('uses semantic time element for date', () => {
      render(<DatasetCard dataset={mockDataset} />);
      
      const timeElement = screen.getByText('15 January 2026').closest('time');
      expect(timeElement).toHaveAttribute('dateTime', mockDataset.modified);
    });
  });
});

