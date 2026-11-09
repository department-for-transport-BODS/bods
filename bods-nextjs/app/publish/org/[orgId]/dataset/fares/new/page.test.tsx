import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import FaresCreatePage, { metadata } from './page';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('FaresCreatePage', () => {
  it('renders the client form and exports its route metadata', () => {
    expect(metadata).toEqual({ title: 'Publish new data set: description' });

    render(<FaresCreatePage />);

    expect(screen.getByLabelText('Data set description')).toBeInTheDocument();
  });
});
