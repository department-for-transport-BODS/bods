import { render, screen, waitFor } from '@testing-library/react';
import { api, ApiError } from '@/lib/api-client';
import AcceptInvitePage from './page';

const mockReplace = jest.fn();
const mockNotFound = jest.fn();
let mockKey = 'abc123';

jest.mock('next/navigation', () => ({
  useParams: () => ({ key: mockKey }),
  useRouter: () => ({ replace: mockReplace }),
  notFound: () => mockNotFound(),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

function renderPage() {
  return render(<AcceptInvitePage />);
}

describe('Accept invitation page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockKey = 'abc123';
  });

  it('posts the invite key and goes to signup when the link is valid', async () => {
    (api.post as jest.Mock).mockResolvedValue({
      email: 'new.operator@example.com',
      isAgent: false,
      organisationName: 'Acme Buses',
    });

    renderPage();

    expect(screen.queryByText('Checking this invitation...')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/invite/accept/', { key: 'abc123' });
    });
    expect(mockReplace).toHaveBeenCalledWith('/account/signup');
  });

  it('shows the expired copy on this URL when the invite is gone', async () => {
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('This invitation link has already been accepted or has expired.', 410, {}),
    );

    renderPage();

    expect(
      await screen.findByText('This invitation link has already been accepted or has expired.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'contacting us.' })).toHaveAttribute(
      'href',
      expect.stringContaining('/contact'),
    );
    expect(mockReplace).not.toHaveBeenCalled();
    expect(screen.queryByText('Checking this invitation...')).not.toBeInTheDocument();
  });

  it('404s for keys Django would not route', () => {
    mockKey = 'not-a-key';

    renderPage();

    expect(mockNotFound).toHaveBeenCalled();
    expect(api.post).not.toHaveBeenCalled();
  });
});
