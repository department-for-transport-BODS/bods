import { render, screen } from '@testing-library/react';
import TimetableChangelogPage from './TimetableChangelogPageContent';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div data-testid="protected">{children}</div>,
}));

jest.mock('@/components/publish/changelog/PublishChangelogPageContent', () => ({
  PublishChangelogPageContent: ({ kind }: { kind: string }) => <p>changelog for {kind}</p>,
}));

describe('TimetableChangelogPage', () => {
  it('guards the timetable changelog with ProtectedRoute', () => {
    render(<TimetableChangelogPage />);
    expect(screen.getByTestId('protected')).toHaveTextContent('changelog for timetables');
  });
});
