import { render, screen } from '@testing-library/react';
import FaresAttentionPage, { metadata } from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div data-testid="protected">{children}</div>,
}));

jest.mock('@/components/publish/requires-attention/RequiresAttentionContent', () => ({
  RequiresAttentionContent: ({ kind }: { kind: string }) => <div>content:{kind}</div>,
}));

describe('Fares - Service codes requiring attention - Page', () => {
  it('sets the Django page title', () => {
    expect(metadata.title).toBe('Service Codes Requiring Attention');
  });

  it('wraps the fares content in ProtectedRoute', () => {
    render(<FaresAttentionPage />);

    expect(screen.getByTestId('protected')).toHaveTextContent('content:fares');
  });
});
