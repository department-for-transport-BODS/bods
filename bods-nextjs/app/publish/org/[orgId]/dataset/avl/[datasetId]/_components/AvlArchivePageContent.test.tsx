import { render, screen } from '@testing-library/react';
import { AvlArchivePageContent } from './AvlArchivePageContent';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '12', datasetId: '34' }),
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: () => new Promise(() => {}) },
  getCsrfToken: () => 'token',
}));

describe('AvlArchivePageContent', () => {
  it('links Back and Cancel to the feed detail page', () => {
    render(<AvlArchivePageContent />);

    for (const name of ['Back', 'Cancel']) {
      const href = screen.getByRole('link', { name }).getAttribute('href');
      expect(href).toMatch(/\/org\/12\/dataset\/avl\/34\/$/);
      expect(href).not.toMatch(/\/publish\/org/);
    }
  });
});
