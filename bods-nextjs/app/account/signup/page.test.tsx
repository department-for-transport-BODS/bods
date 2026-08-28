import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HostProvider } from '@/lib/bods-host-context';
import SignupPage from './page';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('next/link', () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

jest.mock('@/lib/api-client', () => ({
  ensureCsrfToken: async () => 'csrf-token',
}));

function renderSignupPage() {
  return render(
    <HostProvider hostname="data.example.com">
      <SignupPage />
    </HostProvider>,
  );
}

async function completeForm() {
  await userEvent.type(screen.getByLabelText('First Name'), 'Ada');
  await userEvent.type(screen.getByLabelText('Last Name'), 'Lovelace');
  await userEvent.type(screen.getByLabelText('Organisation'), 'Analytical Engines');
  await userEvent.click(screen.getByLabelText('App'));
  await userEvent.type(
    screen.getByLabelText('Please provide a short description about your intended use below.'),
    'A journey planner.',
  );
  await userEvent.click(screen.getByLabelText('National'));

  const shareAppUsage = screen.getByRole('group', { name: /contact you to discuss/ });
  await userEvent.click(within(shareAppUsage).getByLabelText('Yes'));

  const userResearch = screen.getByRole('group', { name: /part of our user research/ });
  await userEvent.click(within(userResearch).getByLabelText('No'));

  await userEvent.type(screen.getByLabelText('Email'), 'consumer@example.com');
  await userEvent.type(screen.getByLabelText('Password'), 'a very Long and compl1c@ted phrase');
  await userEvent.type(
    screen.getByLabelText('Confirm new password'),
    'a very Long and compl1c@ted phrase',
  );
}

describe('Signup page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.sessionStorage.clear();
    global.fetch = jest.fn();
  });

  it('renders the fields Django asks developers for, and no account type choice', () => {
    renderSignupPage();

    expect(screen.getByRole('heading', { name: 'Create account' })).toBeInTheDocument();
    expect(
      screen.getByText('Enter your details to create an account and start using bus open data.'),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('First Name')).toBeInTheDocument();
    expect(screen.getByText('If you do not belong to an organisation, please type N/A')).toBeInTheDocument();
    expect(
      screen.getByRole('group', { name: 'What best describes your intended use?' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('group', { name: 'Which areas of data are you interested in?' }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toHaveAttribute('id', 'email');
    expect(screen.getByLabelText('Password')).toHaveAttribute('id', 'password1');
    expect(screen.getByLabelText('Confirm new password')).toHaveAttribute('id', 'password2');
    expect(screen.queryByLabelText('Account type')).not.toBeInTheDocument();
  });

  it('posts the developer signup payload and goes to the verify email page', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ account_exists: false, email: 'consumer@example.com' }),
    });

    renderSignupPage();
    await completeForm();
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    const [path, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(path).toBe('/api/auth/signup/');
    expect(init.headers['X-CSRFToken']).toBe('csrf-token');
    expect(JSON.parse(init.body)).toEqual({
      first_name: 'Ada',
      last_name: 'Lovelace',
      dev_organisation: 'Analytical Engines',
      intended_use: '1',
      description: 'A journey planner.',
      national_interest: 'True',
      regional_areas: '',
      share_app_usage: 'True',
      opt_in_user_research: 'False',
      email: 'consumer@example.com',
      password1: 'a very Long and compl1c@ted phrase',
      password2: 'a very Long and compl1c@ted phrase',
    });

    expect(mockPush).toHaveBeenCalledWith('/account/confirm-email');
    expect(window.sessionStorage.getItem('bods:verification-email')).toBe('consumer@example.com');
  });

  it('shows field errors from the API', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: async () => ({
        error: 'Validation failed',
        field_errors: { dev_organisation: ['Please provide an Organisation'] },
      }),
    });

    renderSignupPage();
    await completeForm();
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(await screen.findAllByText('Please provide an Organisation')).not.toHaveLength(0);
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('tells the user to sign in when the account already exists', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ account_exists: true }),
    });

    renderSignupPage();
    await completeForm();
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(
      await screen.findByText(
        'An account with this email address has already been registered on BODS. Please click below to sign in.',
      ),
    ).toBeInTheDocument();
    const signInButton = screen
      .getAllByRole('link', { name: 'Sign in' })
      .find((link) => link.classList.contains('govuk-button'));
    expect(signInButton).toHaveAttribute('href', '/account/login');
    expect(mockPush).not.toHaveBeenCalled();
  });
});
