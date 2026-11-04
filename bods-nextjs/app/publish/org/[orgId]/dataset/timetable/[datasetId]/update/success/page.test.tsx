import { render, screen } from '@testing-library/react';
import TimetableUpdateSuccessPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../_components/TimetableUpdateSuccessContent', () => ({
  TimetableUpdateSuccessContent: () => <div data-testid="success" />,
}));

describe('TimetableUpdateSuccessPage', () => {
  it('renders the update success content', () => {
    render(<TimetableUpdateSuccessPage />);

    expect(screen.getByTestId('success')).toBeInTheDocument();
  });
});
