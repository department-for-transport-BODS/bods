import { render, screen } from '@testing-library/react';
import FaresUpdateReviewPage from './page';

jest.mock('next/server', () => ({
  connection: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@/config/server', () => ({
  serverConfig: { mapboxToken: 'pk.server' },
}));

jest.mock('../../review/FaresReviewPageContent', () => ({
  __esModule: true,
  default: ({ mapboxToken, isUpdate }: { mapboxToken: string; isUpdate?: boolean }) => (
    <div data-testid="review">{`${mapboxToken}:${isUpdate ? 'update' : 'publish'}`}</div>
  ),
}));

describe('FaresUpdateReviewPage', () => {
  it('renders the shared fares review in update mode with the server Mapbox token', async () => {
    render(await FaresUpdateReviewPage());

    expect(screen.getByTestId('review')).toHaveTextContent('pk.server:update');
  });
});
