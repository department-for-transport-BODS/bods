/**
 * DownloadSubscribePanel Component Tests
 * 
 * 
 * Tests the download and subscribe panel with various scenarios
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DownloadSubscribePanel } from './DownloadSubscribePanel';

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) => {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('DownloadSubscribePanel', () => {
  const defaultProps = {
    datasetId: 123,
    downloadUrl: 'https://api.example.com/dataset/123/download',
    fileExtension: 'xml',
  };

  describe('Rendering', () => {
    it('renders the section heading', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      expect(screen.getByRole('heading', { 
        name: /subscribe, download the data/i 
      })).toBeInTheDocument();
    });

    it('renders subscribe link when not subscribed', () => {
      render(<DownloadSubscribePanel {...defaultProps} isSubscribed={false} />);
      
      expect(screen.getByText('Subscribe to this data set')).toBeInTheDocument();
    });

    it('renders unsubscribe link when subscribed', () => {
      render(<DownloadSubscribePanel {...defaultProps} isSubscribed={true} />);
      
      expect(screen.getByText('Unsubscribe from this data set')).toBeInTheDocument();
    });

    it('renders download link with correct extension', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      const downloadLink = screen.getByText(/download dataset \(\.xml\)/i);
      expect(downloadLink).toBeInTheDocument();
      expect(downloadLink).toHaveAttribute('href', defaultProps.downloadUrl);
      expect(downloadLink).toHaveAttribute('download');
    });

    it('displays file size when provided', () => {
      render(<DownloadSubscribePanel {...defaultProps} fileSize="2.5 MB" />);
      
      expect(screen.getByText(/2\.5 MB/i)).toBeInTheDocument();
    });

    it('does not display file size when not provided', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      expect(screen.queryByText(/MB|KB|GB/i)).not.toBeInTheDocument();
    });
  });

  describe('Subscribe Interaction', () => {
    it('renders as link when no onSubscribeToggle provided', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      const subscribeLink = screen.getByText('Subscribe to this data set');
      expect(subscribeLink.tagName).toBe('A');
      expect(subscribeLink).toHaveAttribute('href', '/data/123/subscription');
    });

    it('renders as button when onSubscribeToggle provided', () => {
      const mockToggle = jest.fn();
      render(<DownloadSubscribePanel {...defaultProps} onSubscribeToggle={mockToggle} />);
      
      const subscribeButton = screen.getByText('Subscribe to this data set');
      expect(subscribeButton.tagName).toBe('BUTTON');
    });

    it('calls onSubscribeToggle when button clicked', async () => {
      const mockToggle = jest.fn().mockResolvedValue(undefined);
      render(
        <DownloadSubscribePanel 
          {...defaultProps}
          isSubscribed={false}
          onSubscribeToggle={mockToggle}
        />
      );
      
      const subscribeButton = screen.getByText('Subscribe to this data set');
      fireEvent.click(subscribeButton);
      
      await waitFor(() => {
        expect(mockToggle).toHaveBeenCalledWith(true);
      });
    });

    it('toggles subscription state after successful toggle', async () => {
      const mockToggle = jest.fn().mockResolvedValue(undefined);
      render(
        <DownloadSubscribePanel 
          {...defaultProps}
          isSubscribed={false}
          onSubscribeToggle={mockToggle}
        />
      );
      
      const subscribeButton = screen.getByText('Subscribe to this data set');
      fireEvent.click(subscribeButton);
      
      await waitFor(() => {
        expect(screen.getByText('Unsubscribe from this data set')).toBeInTheDocument();
      });
    });

    it('disables button while toggling', async () => {
      let resolveToggle: () => void;
      const togglePromise = new Promise<void>((resolve) => {
        resolveToggle = resolve;
      });
      const mockToggle = jest.fn().mockReturnValue(togglePromise);
      
      render(
        <DownloadSubscribePanel 
          {...defaultProps}
          onSubscribeToggle={mockToggle}
        />
      );
      
      const subscribeButton = screen.getByText('Subscribe to this data set') as HTMLButtonElement;
      fireEvent.click(subscribeButton);
      
      expect(subscribeButton).toBeDisabled();
      
      resolveToggle!();
      await waitFor(() => {
        expect(subscribeButton).not.toBeDisabled();
      });
    });

    it('handles toggle error gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      const mockToggle = jest.fn().mockRejectedValue(new Error('Network error'));
      
      render(
        <DownloadSubscribePanel 
          {...defaultProps}
          isSubscribed={false}
          onSubscribeToggle={mockToggle}
        />
      );
      
      const subscribeButton = screen.getByText('Subscribe to this data set');
      fireEvent.click(subscribeButton);
      
      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
      });
      
      expect(screen.getByText('Subscribe to this data set')).toBeInTheDocument();
      
      consoleErrorSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label on subscribe button', () => {
      const mockToggle = jest.fn();
      render(
        <DownloadSubscribePanel 
          {...defaultProps}
          isSubscribed={false}
          onSubscribeToggle={mockToggle}
        />
      );
      
      const subscribeButton = screen.getByLabelText('Subscribe to this data set');
      expect(subscribeButton).toBeInTheDocument();
    });

    it('has proper aria-label on unsubscribe button', () => {
      const mockToggle = jest.fn();
      render(
        <DownloadSubscribePanel 
          {...defaultProps}
          isSubscribed={true}
          onSubscribeToggle={mockToggle}
        />
      );
      
      const unsubscribeButton = screen.getByLabelText('Unsubscribe from this data set');
      expect(unsubscribeButton).toBeInTheDocument();
    });

    it('has descriptive aria-label on download link with file size', () => {
      render(<DownloadSubscribePanel {...defaultProps} fileSize="2.5 MB" />);
      
      const downloadLink = screen.getByLabelText(/download dataset.*\.xml.*2\.5 MB/i);
      expect(downloadLink).toBeInTheDocument();
    });

    it('uses semantic list markup', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
      expect(list).toHaveClass('govuk-list');
    });
  });

  describe('File Extensions', () => {
    it('displays TransXChange XML extension correctly', () => {
      render(<DownloadSubscribePanel {...defaultProps} fileExtension="xml" />);
      expect(screen.getByText(/\.xml/i)).toBeInTheDocument();
    });

    it('displays NeTEx XML extension correctly', () => {
      render(<DownloadSubscribePanel {...defaultProps} fileExtension="xml" />);
      expect(screen.getByText(/\.xml/i)).toBeInTheDocument();
    });

    it('displays ZIP extension correctly', () => {
      render(<DownloadSubscribePanel {...defaultProps} fileExtension="zip" />);
      expect(screen.getByText(/\.zip/i)).toBeInTheDocument();
    });
  });

  describe('Django Parity', () => {
    it('matches Django template structure', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      expect(screen.getByRole('heading', { 
        name: /subscribe, download the data/i 
      })).toBeInTheDocument();
      
      const list = screen.getByRole('list');
      expect(list).toHaveClass('app-list--nav');
      expect(list).toHaveClass('govuk-!-font-size-19');
    });

    it('matches Django download URL pattern', () => {
      render(<DownloadSubscribePanel {...defaultProps} />);
      
      const downloadLink = screen.getByText(/download dataset/i);
      expect(downloadLink).toHaveAttribute('href', expect.stringContaining('/download'));
    });
  });
});
