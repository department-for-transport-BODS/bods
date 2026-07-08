/**
 * AVL Validation Tests
 *
 * Tests for form validation functions
 */

import {
  validateAvlDescriptionStep,
  validateAvlUploadStep,
  validateAvlCommentStep,
  validateAvlConsentStep,
} from './avl-publish';
import { AVL_PUBLISH_ERRORS } from './messages';

describe('AVL Validation Functions', () => {
  describe('validateAvlDescriptionStep', () => {
    it('returns no errors when both fields are valid', () => {
      const result = validateAvlDescriptionStep({
        description: 'Valid description',
        shortDescription: 'Short desc',
      });

      expect(result).toEqual({});
    });

    it('returns error when description is empty', () => {
      const result = validateAvlDescriptionStep({
        description: '',
        shortDescription: 'Short desc',
      });

      expect(result.description).toBe(AVL_PUBLISH_ERRORS.description);
    });

    it('returns error when description is whitespace only', () => {
      const result = validateAvlDescriptionStep({
        description: '   ',
        shortDescription: 'Short desc',
      });

      expect(result.description).toBe(AVL_PUBLISH_ERRORS.description);
    });

    it('returns error when shortDescription is empty', () => {
      const result = validateAvlDescriptionStep({
        description: 'Valid description',
        shortDescription: '',
      });

      expect(result.shortDescription).toBe(AVL_PUBLISH_ERRORS.shortDescription);
    });

    it('returns error when shortDescription is whitespace only', () => {
      const result = validateAvlDescriptionStep({
        description: 'Valid description',
        shortDescription: '   ',
      });

      expect(result.shortDescription).toBe(AVL_PUBLISH_ERRORS.shortDescription);
    });

    it('returns errors when both fields are empty', () => {
      const result = validateAvlDescriptionStep({
        description: '',
        shortDescription: '',
      });

      expect(result).toHaveProperty('description');
      expect(result).toHaveProperty('shortDescription');
      expect(Object.keys(result)).toHaveLength(2);
    });

    it('handles long descriptions correctly', () => {
      const longDescription = 'A'.repeat(1000);
      const result = validateAvlDescriptionStep({
        description: longDescription,
        shortDescription: 'Short desc',
      });

      expect(result).toEqual({});
    });
  });

  describe('validateAvlUploadStep', () => {
    it('returns no errors when all fields are valid', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result).toEqual({});
    });

    it('returns error when urlLink is empty', () => {
      const result = validateAvlUploadStep({
        urlLink: '',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBe(AVL_PUBLISH_ERRORS.urlLink);
    });

    it('returns error for invalid URL without protocol', () => {
      const result = validateAvlUploadStep({
        urlLink: 'example.com/feed',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBe(AVL_PUBLISH_ERRORS.invalidUrlLink);
    });

    it('returns error for invalid protocol', () => {
      const result = validateAvlUploadStep({
        urlLink: 'ftp://example.com/feed',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBe(AVL_PUBLISH_ERRORS.invalidUrlLink);
    });

    it('accepts http URLs', () => {
      const result = validateAvlUploadStep({
        urlLink: 'http://example.com/feed',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBeUndefined();
    });

    it('accepts https URLs', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBeUndefined();
    });

    it('returns error when username is empty', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed',
        username: '',
        password: 'testpass',
      });

      expect(result.username).toBe(AVL_PUBLISH_ERRORS.username);
    });

    it('returns error when username is whitespace only', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed',
        username: '   ',
        password: 'testpass',
      });

      expect(result.username).toBe(AVL_PUBLISH_ERRORS.username);
    });

    it('returns error when password is empty', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed',
        username: 'testuser',
        password: '',
      });

      expect(result.password).toBe(AVL_PUBLISH_ERRORS.password);
    });

    it('returns error when password is whitespace only', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed',
        username: 'testuser',
        password: '   ',
      });

      expect(result.password).toBe(AVL_PUBLISH_ERRORS.password);
    });

    it('returns multiple errors when multiple fields are invalid', () => {
      const result = validateAvlUploadStep({
        urlLink: 'invalid-url',
        username: '',
        password: '',
      });

      expect(result).toHaveProperty('urlLink');
      expect(result).toHaveProperty('username');
      expect(result).toHaveProperty('password');
    });

    it('handles URLs with query parameters', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com/feed?key=value&param=test',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBeUndefined();
    });

    it('handles URLs with ports', () => {
      const result = validateAvlUploadStep({
        urlLink: 'https://example.com:8080/feed',
        username: 'testuser',
        password: 'testpass',
      });

      expect(result.urlLink).toBeUndefined();
    });
  });

  describe('validateAvlCommentStep', () => {
    it('returns no errors when comment is provided', () => {
      const result = validateAvlCommentStep({ comment: 'This is a valid comment' });

      expect(result).toEqual({});
    });

    it('returns error when comment is empty', () => {
      const result = validateAvlCommentStep({ comment: '' });

      expect(result.comment).toBe(AVL_PUBLISH_ERRORS.comment);
    });

    it('returns error when comment is whitespace only', () => {
      const result = validateAvlCommentStep({ comment: '   ' });

      expect(result.comment).toBe(AVL_PUBLISH_ERRORS.comment);
    });

    it('returns error when comment is only tabs and newlines', () => {
      const result = validateAvlCommentStep({ comment: '\t\n\r' });

      expect(result.comment).toBe(AVL_PUBLISH_ERRORS.comment);
    });

    it('accepts long comments', () => {
      const longComment = 'A'.repeat(5000);
      const result = validateAvlCommentStep({ comment: longComment });

      expect(result).toEqual({});
    });

    it('accepts comments with special characters', () => {
      const result = validateAvlCommentStep({
        comment: 'Comment with @#$%^&*() special chars',
      });

      expect(result).toEqual({});
    });
  });

  describe('validateAvlConsentStep', () => {
    it('returns no errors when consent is checked', () => {
      const result = validateAvlConsentStep(true);

      expect(result).toEqual({});
    });

    it('returns error when consent is not checked', () => {
      const result = validateAvlConsentStep(false);

      expect(result.consent).toBe(AVL_PUBLISH_ERRORS.consent);
    });

    it('returns error when consent is false', () => {
      const result = validateAvlConsentStep(false);

      expect(Object.keys(result)).toHaveLength(1);
      expect(result).toHaveProperty('consent');
    });
  });
});
