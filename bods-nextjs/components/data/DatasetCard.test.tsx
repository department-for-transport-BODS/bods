/**
 * DatasetCard Component Tests
 * 
 */

import { render, screen } from '@testing-library/react';
import { DatasetCard } from './DatasetCard';
import type { DatasetListItem } from '@/types';

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
    
    const badge = screen.getByText('85.5%');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('govuk-tag--green');
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
    it('displays green badge for green RAG status', () => {
      const dataset = { ...mockDataset, dqRag: 'green' as const };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('85.5%');
      expect(badge).toHaveClass('govuk-tag--green');
    });

    it('displays yellow badge for amber RAG status', () => {
      const dataset = { ...mockDataset, dqRag: 'amber' as const, dqScore: '65.0%' };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('65.0%');
      expect(badge).toHaveClass('govuk-tag--yellow');
    });

    it('displays red badge for red RAG status', () => {
      const dataset = { ...mockDataset, dqRag: 'red' as const, dqScore: '30.0%' };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('30.0%');
      expect(badge).toHaveClass('govuk-tag--red');
    });

    it('displays grey badge with N/A for unavailable RAG status', () => {
      const dataset = { ...mockDataset, dqRag: 'unavailable' as const };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('N/A');
      expect(badge).toHaveClass('govuk-tag--grey');
    });
  });

  describe('data type badges', () => {
    it('displays blue badge for TIMETABLE type', () => {
      const dataset = { ...mockDataset, dataType: 'TIMETABLE' as const };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('Timetable');
      expect(badge).toHaveClass('govuk-tag--blue');
    });

    it('displays purple badge for AVL type', () => {
      const dataset = { ...mockDataset, dataType: 'AVL' as const };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('Location');
      expect(badge).toHaveClass('govuk-tag--purple');
    });

    it('displays turquoise badge for FARES type', () => {
      const dataset = { ...mockDataset, dataType: 'FARES' as const };
      render(<DatasetCard dataset={dataset} />);
      
      const badge = screen.getByText('Fares');
      expect(badge).toHaveClass('govuk-tag--turquoise');
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
      
      const badge = screen.getByText('85.5%');
      expect(badge).toHaveAttribute('aria-label', 'Quality: 85.5%');
    });

    it('uses semantic time element for date', () => {
      render(<DatasetCard dataset={mockDataset} />);
      
      const timeElement = screen.getByText('15 January 2026').closest('time');
      expect(timeElement).toHaveAttribute('dateTime', mockDataset.modified);
    });
  });
});

