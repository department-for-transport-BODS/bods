import { render, screen } from '@testing-library/react';
import { headers } from 'next/headers';
import { notFound } from 'next/navigation';
import Page from './page';

const mockReplace = jest.fn();

jest.mock('next/headers', () => ({ headers: jest.fn() }));

jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace }),
  notFound: jest.fn(() => {
    throw new Error('NEXT_NOT_FOUND');
  }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

function mockHost(host: string) {
  (headers as jest.Mock).mockResolvedValue(new Headers({ host }));
}

describe('account/~redirect page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it.each(['data.localhost:3000', 'publish.localhost:3000', 'admin.localhost:3000'])(
    'redirects signed-in users to the home page of the %s host',
    async (host) => {
      mockHost(host);

      render(await Page());

      expect(screen.getByText('Redirecting...')).toBeInTheDocument();
      expect(mockReplace).toHaveBeenCalledWith('/');
      expect(notFound).not.toHaveBeenCalled();
    },
  );

  it('is not found on the www host, where Django does not mount it', async () => {
    mockHost('localhost:3000');

    await expect(Page()).rejects.toThrow('NEXT_NOT_FOUND');
    expect(notFound).toHaveBeenCalled();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
