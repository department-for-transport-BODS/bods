import { render, screen } from '@testing-library/react';
import FaresChangelogPage from './FaresChangelogPageContent';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div data-testid="protected">{children}</div>,
}));

jest.mock('@/components/publish/changelog/PublishChangelogPageContent', () => ({
  PublishChangelogPageContent: ({ kind }: { kind: string }) => <p>changelog for {kind}</p>,
}));

describe('FaresChangelogPage', () => {
  it('guards the fares changelog with ProtectedRoute', () => {
    render(<FaresChangelogPage />);
    expect(screen.getByTestId('protected')).toHaveTextContent('changelog for fares');
  });
});
