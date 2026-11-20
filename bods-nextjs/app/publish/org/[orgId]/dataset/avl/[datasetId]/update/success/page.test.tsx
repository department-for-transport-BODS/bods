import { render, screen } from '@testing-library/react';
import AVLUpdateSuccessPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../_components/AvlSuccessPanel', () => ({
  AvlSuccessPanel: ({ update }: { update: boolean }) => (
    <div data-testid="success-panel">{update ? 'update' : 'create'}</div>
  ),
}));

describe('AVLUpdateSuccessPage', () => {
  it('renders success panel for update flow', () => {
    render(<AVLUpdateSuccessPage />);

    expect(screen.getByTestId('success-panel')).toHaveTextContent('update');
  });
});
