/**
 * AVL Status Utility Tests
 *
 * Tests for status indicator classes and labels
 */

import { statusIndicatorClass, statusLabel } from './avlStatus';

describe('avlStatus utilities', () => {
  describe('statusIndicatorClass', () => {
    it('returns success class for "published" status', () => {
      expect(statusIndicatorClass('published')).toBe('status-indicator--success');
    });

    it('returns success class for "live" status', () => {
      expect(statusIndicatorClass('live')).toBe('status-indicator--success');
    });

    it('returns draft class for "draft" status', () => {
      expect(statusIndicatorClass('draft')).toBe('status-indicator--draft');
    });

    it('returns error class for "error" status', () => {
      expect(statusIndicatorClass('error')).toBe('status-indicator--error');
    });

    it('returns warning class for "warning" status', () => {
      expect(statusIndicatorClass('warning')).toBe('status-indicator--warning');
    });

    it('returns indexing class for "indexing" status', () => {
      expect(statusIndicatorClass('indexing')).toBe('status-indicator--indexing');
    });

    it('returns indexing class for "pending" status', () => {
      expect(statusIndicatorClass('pending')).toBe('status-indicator--indexing');
    });

    it('returns indexing class for "processing" status', () => {
      expect(statusIndicatorClass('processing')).toBe('status-indicator--indexing');
    });

    it('returns draft class for undefined status', () => {
      expect(statusIndicatorClass()).toBe('status-indicator--draft');
    });

    it('returns draft class for unknown status', () => {
      expect(statusIndicatorClass('unknown_status')).toBe('status-indicator--draft');
    });
  });

  describe('statusLabel', () => {
    it('returns "Published" for "published" status', () => {
      expect(statusLabel('published')).toBe('Published');
    });

    it('returns "Published" for "live" status', () => {
      expect(statusLabel('live')).toBe('Published');
    });

    it('returns "Draft" for "draft" status', () => {
      expect(statusLabel('draft')).toBe('Draft');
    });

    it('returns "Draft" for "success" status', () => {
      expect(statusLabel('success')).toBe('Draft');
    });

    it('returns "Processing" for "indexing" status', () => {
      expect(statusLabel('indexing')).toBe('Processing');
    });

    it('returns "Processing" for "pending" status', () => {
      expect(statusLabel('pending')).toBe('Processing');
    });

    it('returns "Processing" for "processing" status', () => {
      expect(statusLabel('processing')).toBe('Processing');
    });

    it('returns "Draft" for undefined status', () => {
      expect(statusLabel()).toBe('Draft');
    });

    it('capitalizes unknown status strings', () => {
      expect(statusLabel('warning')).toBe('Warning');
      expect(statusLabel('error')).toBe('Error');
    });

    it('capitalizes first letter for arbitrary status', () => {
      expect(statusLabel('archived')).toBe('Archived');
      expect(statusLabel('inactive')).toBe('Inactive');
    });
  });
});
