/**
 * DataQualityBadge Component Tests
 * 
 * 
 * Tests the data quality badge component with various RAG states,
 * tooltips, accessibility features, and link behavior.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DataQualityBadge } from './DataQualityBadge';

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) => {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('DataQualityBadge', () => {
  describe('RAG Status Display', () => {
    it('renders green badge for high quality score', () => {
      render(<DataQualityBadge score="100%" rag="green" />);
      
      expect(screen.getByText(/100% GREEN/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/data quality score: 100%, rated GREEN/i)).toBeInTheDocument();
    });

    it('renders amber badge for moderate quality score', () => {
      render(<DataQualityBadge score="95%" rag="amber" />);
      
      expect(screen.getByText(/95% AMBER/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/data quality score: 95%, rated AMBER/i)).toBeInTheDocument();
    });

    it('renders red badge for low quality score', () => {
      render(<DataQualityBadge score="85%" rag="red" />);
      
      expect(screen.getByText(/85% RED/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/data quality score: 85%, rated RED/i)).toBeInTheDocument();
    });

    it('does not render when quality is unavailable', () => {
      const { container } = render(<DataQualityBadge score="N/A" rag="unavailable" />);
      
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Tooltip Display', () => {
    it('shows tooltip for green status by default', () => {
      render(<DataQualityBadge score="100%" rag="green" />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).toHaveAttribute('title', expect.stringContaining('high quality score'));
      expect(badge).toHaveAttribute('title', expect.stringContaining('100%'));
    });

    it('shows tooltip for amber status', () => {
      render(<DataQualityBadge score="92%" rag="amber" />);
      
      const badge = screen.getByLabelText(/data quality score: 92%, rated AMBER/i);
      expect(badge).toHaveAttribute('title', expect.stringContaining('moderate quality score'));
      expect(badge).toHaveAttribute('title', expect.stringContaining('minor issues'));
    });

    it('shows tooltip for red status', () => {
      render(<DataQualityBadge score="85%" rag="red" />);
      
      const badge = screen.getByLabelText(/data quality score: 85%, rated RED/i);
      expect(badge).toHaveAttribute('title', expect.stringContaining('low quality score'));
      expect(badge).toHaveAttribute('title', expect.stringContaining('need attention'));
    });

    it('does not show tooltip when showTooltip is false', () => {
      render(<DataQualityBadge score="100%" rag="green" showTooltip={false} />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).not.toHaveAttribute('title');
    });
  });

  describe('Link Behavior', () => {
    it('renders as link when reportUrl is provided (inline variant)', () => {
      render(
        <DataQualityBadge 
          score="95%" 
          rag="green" 
          reportUrl="/quality-report/123"
          variant="inline"
        />
      );
      
      const link = screen.getByRole('link', { name: /view full data quality report/i });
      expect(link).toHaveAttribute('href', '/quality-report/123');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders as plain text when no reportUrl (inline variant)', () => {
      render(
        <DataQualityBadge 
          score="95%" 
          rag="green"
          variant="inline"
        />
      );
      
      expect(screen.queryByRole('link')).not.toBeInTheDocument();
      expect(screen.getByText(/95% GREEN/i)).toBeInTheDocument();
    });

    it('renders with link in stacked variant', () => {
      render(
        <DataQualityBadge 
          score="90%" 
          rag="amber"
          reportUrl="/quality-report/456"
          variant="stacked"
        />
      );
      
      const link = screen.getByRole('link', { name: /view full data quality report/i });
      expect(link).toHaveAttribute('href', '/quality-report/456');
      expect(screen.getByText('Data quality')).toBeInTheDocument();
    });
  });

  describe('Variant Styles', () => {
    it('renders inline variant by default', () => {
      const { container } = render(<DataQualityBadge score="100%" rag="green" />);
      
      expect(container.querySelector('.dq-badge-stacked')).not.toBeInTheDocument();
    });

    it('renders stacked variant with label', () => {
      render(
        <DataQualityBadge 
          score="95%" 
          rag="green"
          variant="stacked"
        />
      );
      
      expect(screen.getByText('Data quality')).toBeInTheDocument();
      expect(screen.getByText(/95% GREEN/i)).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('applies default medium size', () => {
      render(<DataQualityBadge score="100%" rag="green" size="medium" />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).toHaveStyle({ fontSize: 'inherit' });
    });

    it('applies small size', () => {
      render(<DataQualityBadge score="100%" rag="green" size="small" />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).toHaveStyle({ fontSize: '0.875rem' });
    });

    it('applies large size', () => {
      render(<DataQualityBadge score="100%" rag="green" size="large" />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).toHaveStyle({ fontSize: '1.25rem' });
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label for screen readers', () => {
      render(<DataQualityBadge score="87%" rag="red" />);
      
      const badge = screen.getByLabelText('Data quality score: 87%, rated RED');
      expect(badge).toBeInTheDocument();
    });

    it('has descriptive link aria-label when reportUrl provided', () => {
      render(
        <DataQualityBadge 
          score="92%" 
          rag="amber"
          reportUrl="/report/123"
        />
      );
      
      const link = screen.getByRole('link', { 
        name: /view full data quality report.*92%.*AMBER/i 
      });
      expect(link).toBeInTheDocument();
    });

    it('includes title attribute for tooltip accessibility', () => {
      render(<DataQualityBadge score="100%" rag="green" />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).toHaveAttribute('title');
    });
  });

  describe('CSS Indicator Classes', () => {
    it('applies success class for green status', () => {
      render(<DataQualityBadge score="100%" rag="green" />);
      
      const badge = screen.getByLabelText(/data quality score: 100%, rated GREEN/i);
      expect(badge).toHaveClass('status-indicator--success');
    });

    it('applies warning class for amber status', () => {
      render(<DataQualityBadge score="95%" rag="amber" />);
      
      const badge = screen.getByLabelText(/data quality score: 95%, rated AMBER/i);
      expect(badge).toHaveClass('status-indicator--warning');
    });

    it('applies error class for red status', () => {
      render(<DataQualityBadge score="85%" rag="red" />);
      
      const badge = screen.getByLabelText(/data quality score: 85%, rated RED/i);
      expect(badge).toHaveClass('status-indicator--error');
    });
  });

  describe('Edge Cases', () => {
    it('handles score with decimal places', () => {
      render(<DataQualityBadge score="87.5%" rag="red" />);
      
      expect(screen.getByText(/87\.5% RED/i)).toBeInTheDocument();
    });

    it('handles score without percentage symbol', () => {
      render(<DataQualityBadge score="95" rag="amber" />);
      
      expect(screen.getByText(/95 AMBER/i)).toBeInTheDocument();
    });

    it('renders correctly in stacked variant without link', () => {
      render(
        <DataQualityBadge 
          score="100%" 
          rag="green"
          variant="stacked"
        />
      );
      
      expect(screen.getByText('Data quality')).toBeInTheDocument();
      expect(screen.getByText(/100% GREEN/i)).toBeInTheDocument();
      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
  });

  describe('Django Parity', () => {
    it('matches Django RAG threshold display (GREEN >= 100%)', () => {
      render(<DataQualityBadge score="100%" rag="green" />);
      expect(screen.getByText(/100% GREEN/i)).toBeInTheDocument();
    });

    it('matches Django RAG threshold display (AMBER > 90%)', () => {
      render(<DataQualityBadge score="95%" rag="amber" />);
      expect(screen.getByText(/95% AMBER/i)).toBeInTheDocument();
    });

    it('matches Django RAG threshold display (RED <= 90%)', () => {
      render(<DataQualityBadge score="89%" rag="red" />);
      expect(screen.getByText(/89% RED/i)).toBeInTheDocument();
    });

    it('matches Django status-indicator CSS pattern', () => {
      render(<DataQualityBadge score="100%" rag="green" />);
      
      const badge = screen.getByLabelText(/data quality score/i);
      expect(badge).toHaveClass('status-indicator');
      expect(badge).toHaveClass('status-indicator--success');
    });
  });
});
