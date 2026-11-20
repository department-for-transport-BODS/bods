import { render, screen } from '@testing-library/react';
import FaresUpdateSuccessPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../_components/FaresPublishSuccessPanel', () => ({
  FaresPublishSuccessPanel: ({ update }: { update?: boolean }) => (
    <div data-testid="panel">{update ? 'update' : 'publish'}</div>
  ),
}));

describe('FaresUpdateSuccessPage', () => {
  it('renders the success panel in update mode', () => {
    render(<FaresUpdateSuccessPage />);

    expect(screen.getByTestId('panel')).toHaveTextContent('update');
  });
});
