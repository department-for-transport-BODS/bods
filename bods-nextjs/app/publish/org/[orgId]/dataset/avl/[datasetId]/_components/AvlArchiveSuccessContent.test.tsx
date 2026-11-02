import { render, screen } from '@testing-library/react';
import { AvlArchiveSuccessContent } from './AvlArchiveSuccessContent';
import { publishAppPath } from '@/config/client';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '7', datasetId: '9' }),
  useSearchParams: () => new URLSearchParams('name=My feed'),
}));

describe('AvlArchiveSuccessContent', () => {
  it('links Go back to the public data feed list like Django', () => {
    render(<AvlArchiveSuccessContent />);

    expect(screen.getByText('Data feed My feed has been deactivated.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to your data feeds' })).toHaveAttribute(
      'href',
      publishAppPath('/org/7/dataset/avl/'),
    );
  });
});
