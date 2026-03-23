/**
 * ApiUrlPanel Component Tests
 * 
 * 
 * Tests the API URL panel with copy to clipboard functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ApiUrlPanel } from './ApiUrlPanel';

Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

describe('ApiUrlPanel', () => {
  const defaultProps = {
    apiUrl: 'https://api.example.com/v1/dataset/123',
  };

  beforeEach(() => {
    (navigator.clipboard.writeText as jest.Mock).mockClear();
  });

  describe('Rendering', () => {
    it('renders with default title for timetable dataset', () => {
      render(<ApiUrlPanel {...defaultProps} datasetType="TIMETABLE" />);
      
      expect(screen.getByRole('heading', { 
        name: /use this data set in your code/i 
      })).toBeInTheDocument();
    });

    it('renders with specific title for AVL dataset', () => {
      render(<ApiUrlPanel {...defaultProps} datasetType="AVL" />);
      
      expect(screen.getByRole('heading', { 
        name: /use this data feed in your code/i 
      })).toBeInTheDocument();
    });

    it('renders with custom title when provided', () => {
      render(<ApiUrlPanel {...defaultProps} title="Custom API Access" />);
      
      expect(screen.getByRole('heading', { 
        name: /custom api access/i 
      })).toBeInTheDocument();
    });

    it('displays the API URL', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const urlElement = screen.getByText(defaultProps.apiUrl);
      expect(urlElement).toBeInTheDocument();
      expect(urlElement).toHaveClass('api-url-panel__url');
    });

    it('renders copy button', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByRole('button', { name: /copy api endpoint url to clipboard/i });
      expect(copyButton).toBeInTheDocument();
      expect(copyButton).toHaveTextContent('Copy');
    });
  });

  describe('Copy Functionality', () => {
    it('copies URL to clipboard when button clicked', async () => {
      (navigator.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);
      
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(defaultProps.apiUrl);
      });
    });

    it('shows "Copied!" feedback after successful copy', async () => {
      (navigator.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);
      
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(copyButton).toHaveTextContent('Copied!');
      });
    });

    it('reverts button text after 2 seconds', async () => {
      jest.useFakeTimers();
      (navigator.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);
      
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(copyButton).toHaveTextContent('Copied!');
      });
      
      jest.advanceTimersByTime(2000);
      
      await waitFor(() => {
        expect(copyButton).toHaveTextContent('Copy');
      });
      
      jest.useRealTimers();
    });

    it('handles copy error gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      (navigator.clipboard.writeText as jest.Mock).mockRejectedValue(new Error('Clipboard error'));
      
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
      });
      
      expect(copyButton).toHaveTextContent('Copy');
      
      consoleErrorSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label on copy button', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByLabelText('Copy API endpoint URL to clipboard');
      expect(copyButton).toBeInTheDocument();
    });

    it('has aria-label on URL display', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const urlElement = screen.getByLabelText('API endpoint URL');
      expect(urlElement).toBeInTheDocument();
    });

    it('marks URL as readonly', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const urlElement = screen.getByLabelText('API endpoint URL');
      expect(urlElement).toHaveAttribute('aria-readonly', 'true');
    });

    it('uses semantic heading', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const heading = screen.getByRole('heading', { level: 2 });
      expect(heading).toHaveClass('govuk-heading-m');
    });
  });

  describe('URL Display', () => {
    it('displays long URLs correctly', () => {
      const longUrl = 'https://api.example.com/v1/dataset/123/download?format=xml&include=metadata';
      render(<ApiUrlPanel {...defaultProps} apiUrl={longUrl} />);
      
      const urlElement = screen.getByText(longUrl);
      expect(urlElement).toHaveClass('dont-break-out');
    });

    it('uses monospace font for URL', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const urlElement = screen.getByText(defaultProps.apiUrl);
      expect(urlElement).toHaveClass('api-url-panel__url');
    });
  });

  describe('Visual Styling', () => {
    it('applies GDS button styling to copy button', () => {
      render(<ApiUrlPanel {...defaultProps} />);
      
      const copyButton = screen.getByRole('button', { name: /copy/i });
      expect(copyButton).toHaveClass('govuk-button');
      expect(copyButton).toHaveClass('govuk-button--secondary');
    });

    it('has proper panel background', () => {
      const { container } = render(<ApiUrlPanel {...defaultProps} />);
      
      const panel = container.querySelector('.api-url-panel');
      expect(panel).toBeInTheDocument();
    });
  });

  describe('Dataset Type Handling', () => {
    it('handles TIMETABLE type correctly', () => {
      render(<ApiUrlPanel {...defaultProps} datasetType="TIMETABLE" />);
      expect(screen.getByText(/use this data set in your code/i)).toBeInTheDocument();
    });

    it('handles AVL type correctly', () => {
      render(<ApiUrlPanel {...defaultProps} datasetType="AVL" />);
      expect(screen.getByText(/use this data feed in your code/i)).toBeInTheDocument();
    });

    it('handles FARES type correctly', () => {
      render(<ApiUrlPanel {...defaultProps} datasetType="FARES" />);
      expect(screen.getByText(/use this data set in your code/i)).toBeInTheDocument();
    });
  });
});
