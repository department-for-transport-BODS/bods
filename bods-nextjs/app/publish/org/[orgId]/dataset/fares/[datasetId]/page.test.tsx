import { render, screen } from '@testing-library/react';
import { publishAppPath, wwwPath } from '@/config/client';
import { api } from '@/lib/api-client';
import FaresDatasetDetailPage from './page';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '7', datasetId: '42' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

describe('FaresDatasetDetailPage', () => {
  beforeEach(() => {
    (api.get as jest.Mock).mockResolvedValue({
      datasetId: 42,
      status: 'live',
      name: 'Fares data set name long',
      description: 'Full description',
      shortDescription: 'Short',
    });
  });

  it('links to the Django targets for editing, updating and help', async () => {
    render(<FaresDatasetDetailPage />);
    const datasetUrl = publishAppPath('/org/7/dataset/fares/42');

    const editLinks = await screen.findAllByRole('link', { name: 'Edit' });
    expect(editLinks.map((link) => link.getAttribute('href'))).toEqual([
      `${datasetUrl}/dataset-edit/`,
      `${datasetUrl}/dataset-edit/`,
    ]);
    expect(screen.getByText('Full description').closest('td')).toContainElement(editLinks[0]);
    expect(screen.getByText('Short').closest('td')).toContainElement(editLinks[1]);

    expect(screen.getByRole('link', { name: 'Update data set' })).toHaveAttribute('href', `${datasetUrl}/update`);
    expect(screen.getByRole('link', { name: 'Deactivate data set' })).toHaveAttribute(
      'href',
      `${datasetUrl}/deactivate`,
    );
    expect(screen.getByRole('link', { name: 'Fares data set name...' })).toHaveAttribute('href', datasetUrl);
    expect(screen.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      publishAppPath('/guidance/operator-requirements'),
    );
    expect(screen.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute('href', wwwPath('/contact'));
    expect(document.title).toBe('Data set detail');
  });
});
