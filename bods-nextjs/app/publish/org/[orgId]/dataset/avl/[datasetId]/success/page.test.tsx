import { render, screen } from '@testing-library/react';
import AVLPublishSuccessPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../_components/AvlSuccessPanel', () => ({
  AvlSuccessPanel: ({ update }: { update: boolean }) => (
    <div data-testid="success-panel">{update ? 'update' : 'create'}</div>
  ),
}));

describe('AVLPublishSuccessPage', () => {
  it('renders success panel for create flow', () => {
    render(<AVLPublishSuccessPage />);

    expect(screen.getByTestId('success-panel')).toHaveTextContent('create');
  });
});
