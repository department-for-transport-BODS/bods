/**
 * AvlSuccessPanel Component Tests
 *
 * Tests for AVL publish/update success confirmation page
 */

import { render, screen } from '@testing-library/react';
import { AvlSuccessPanel } from './AvlSuccessPanel';

const mockUseParams = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('AvlSuccessPanel', () => {
  const mockParams = {
    orgId: 'org-123',
    datasetId: 'dataset-456',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue(mockParams);
  });

  describe('Published mode (update=false)', () => {
    it('displays success message for published feed', () => {
      render(<AvlSuccessPanel update={false} />);

      expect(screen.getByText(/Your data feed has been successfully published/i)).toBeInTheDocument();
    });

    it('renders confirmation panel', () => {
      render(<AvlSuccessPanel update={false} />);

      const panel = screen.getByText(/Your data feed has been successfully published/i).closest('.govuk-panel');
      expect(panel).toHaveClass('govuk-panel--confirmation');
    });

    it('displays confirmation email message', () => {
      render(<AvlSuccessPanel update={false} />);

      expect(screen.getByText(/We have sent you a confirmation email/i)).toBeInTheDocument();
    });

    it('displays "What happens next?" section', () => {
      render(<AvlSuccessPanel update={false} />);

      expect(screen.getByText('What happens next?')).toBeInTheDocument();
    });

    it('provides link to data feeds list', () => {
      render(<AvlSuccessPanel update={false} />);

      const link = screen.getByRole('link', { name: /data feeds page/i });
      expect(link).toHaveAttribute('href', '/publish/org/org-123/dataset/avl');
    });

    it('provides button to view published feed', () => {
      render(<AvlSuccessPanel update={false} />);

      const button = screen.getByRole('button', { name: /View published data feed/i });
      expect(button).toHaveAttribute('href', '/publish/org/org-123/dataset/avl/dataset-456');
      expect(button).toHaveClass('govuk-button');
    });

    it('displays guidance about SIRI-VM validator', () => {
      render(<AvlSuccessPanel update={false} />);

      expect(screen.getAllByText(/SIRI-VM validator/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/check the mandatory fields are populated 24 hours after publishing/i)).toBeInTheDocument();
    });

    it('includes link to guidance page', () => {
      render(<AvlSuccessPanel update={false} />);

      const guidanceLink = screen.getByRole('link', { name: /guidance page/i });
      expect(guidanceLink).toHaveAttribute('href', '/guidance/support/bus-operators?section=buslocation');
    });

    it('mentions compliance error status', () => {
      render(<AvlSuccessPanel update={false} />);

      expect(screen.getByText(/compliance error status/i)).toBeInTheDocument();
      expect(screen.getByText(/end of 7 days/i)).toBeInTheDocument();
    });
  });

  describe('Updated mode (update=true)', () => {
    it('displays success message for updated feed', () => {
      render(<AvlSuccessPanel update={true} />);

      expect(screen.getByText(/Your data feed has been successfully updated/i)).toBeInTheDocument();
    });

    it('renders confirmation panel for update', () => {
      render(<AvlSuccessPanel update={true} />);

      const panel = screen.getByText(/Your data feed has been successfully updated/i).closest('.govuk-panel');
      expect(panel).toHaveClass('govuk-panel--confirmation');
    });

    it('still displays confirmation email message', () => {
      render(<AvlSuccessPanel update={true} />);

      expect(screen.getByText(/We have sent you a confirmation email/i)).toBeInTheDocument();
    });

    it('still provides link to data feeds list', () => {
      render(<AvlSuccessPanel update={true} />);

      const link = screen.getByRole('link', { name: /data feeds page/i });
      expect(link).toHaveAttribute('href', '/publish/org/org-123/dataset/avl');
    });

    it('still provides button to view updated feed', () => {
      render(<AvlSuccessPanel update={true} />);

      const button = screen.getByRole('button', { name: /View published data feed/i });
      expect(button).toHaveAttribute('href', '/publish/org/org-123/dataset/avl/dataset-456');
    });
  });

  describe('URL generation', () => {
    it('constructs correct list URL with org ID', () => {
      mockUseParams.mockReturnValue({
        orgId: 'test-org-123',
        datasetId: 'test-dataset-456',
      });

      render(<AvlSuccessPanel update={false} />);

      const link = screen.getByRole('link', { name: /data feeds page/i });
      expect(link).toHaveAttribute('href', '/publish/org/test-org-123/dataset/avl');
    });

    it('constructs correct detail URL with org ID and dataset ID', () => {
      mockUseParams.mockReturnValue({
        orgId: 'test-org-789',
        datasetId: 'test-dataset-999',
      });

      render(<AvlSuccessPanel update={false} />);

      const button = screen.getByRole('button', { name: /View published data feed/i });
      expect(button).toHaveAttribute('href', '/publish/org/test-org-789/dataset/avl/test-dataset-999');
    });
  });

  describe('Content and accessibility', () => {
    it('renders as semantic HTML', () => {
      render(<AvlSuccessPanel update={false} />);

      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
    });

    it('displays all informational paragraphs', () => {
      const { container } = render(<AvlSuccessPanel update={false} />);

      const paragraphs = container.querySelectorAll('p.govuk-body-m');
      expect(paragraphs.length).toBeGreaterThan(2);
    });

    it('all links are keyboard navigable', () => {
      render(<AvlSuccessPanel update={false} />);

      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);

      links.forEach((link) => {
        expect(link).toHaveAttribute('href');
      });
    });

    it('button has correct styling classes', () => {
      render(<AvlSuccessPanel update={false} />);

      const button = screen.getByRole('button', { name: /View published data feed/i });
      expect(button).toHaveClass('govuk-button');
    });
  });

  describe('Section breaks', () => {
    it('renders horizontal rule section breaks', () => {
      const { container } = render(<AvlSuccessPanel update={false} />);

      const hrs = container.querySelectorAll('hr.govuk-section-break');
      expect(hrs.length).toBeGreaterThan(0);
    });
  });
});
