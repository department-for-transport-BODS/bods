import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api, ApiError } from '@/lib/api-client';
import { HostProvider } from '@/lib/bods-host-context';
import SignupPage from './page';

const mockPush = jest.fn();
const mockGoHome = jest.fn();

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

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

jest.mock('@/lib/auth/post-signup-redirect', () => ({
  goToSignedInHome: (...args: unknown[]) => mockGoHome(...args),
}));

function renderSignupPage() {
  return render(
    <HostProvider hostname="data.example.com">
      <SignupPage />
    </HostProvider>,
  );
}

async function completeDeveloperForm() {
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
    (api.get as jest.Mock).mockResolvedValue({ mode: 'developer' });
  });

  it('renders the fields Django asks developers for, and no account type choice', async () => {
    renderSignupPage();

    expect(await screen.findByLabelText('First Name')).toBeInTheDocument();
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
    (api.post as jest.Mock).mockResolvedValue({
      account_exists: false,
      email: 'consumer@example.com',
    });

    renderSignupPage();
    await screen.findByLabelText('First Name');
    await completeDeveloperForm();
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());

    expect(api.post).toHaveBeenCalledWith('/api/auth/signup/', {
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
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('Validation failed', 400, {
        dev_organisation: ['Please provide an Organisation'],
      }),
    );

    renderSignupPage();
    await screen.findByLabelText('First Name');
    await completeDeveloperForm();
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(await screen.findAllByText('Please provide an Organisation')).not.toHaveLength(0);
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('goes to account-exists when the account is already registered', async () => {
    (api.post as jest.Mock).mockResolvedValue({ account_exists: true });

    renderSignupPage();
    await screen.findByLabelText('First Name');
    await completeDeveloperForm();
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/account/account-exists');
    });
    expect(
      screen.queryByText(
        'An account with this email address has already been registered on BODS. Please click below to sign in.',
      ),
    ).not.toBeInTheDocument();
  });

  it('renders the operator invite form with a readonly email', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      mode: 'operator',
      email: 'new.operator@example.com',
      organisationName: 'Acme Buses',
    });

    renderSignupPage();

    const email = await screen.findByLabelText('Email*');
    expect(email).toHaveValue('new.operator@example.com');
    expect(email).toHaveAttribute('readOnly');
    expect(screen.getByLabelText('Password*')).toHaveAttribute('id', 'password1');
    expect(screen.getByLabelText('Confirm new password*')).toHaveAttribute('id', 'password2');
    expect(
      screen.getByLabelText(
        'If you are willing to be contacted as part of user research, please tick this box.*',
      ),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText('First Name')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Organisation*')).not.toBeInTheDocument();
  });

  it('posts the operator payload and goes home when the API signs the user in', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      mode: 'operator',
      email: 'new.operator@example.com',
      organisationName: 'Acme Buses',
    });
    (api.post as jest.Mock).mockResolvedValue({
      account_exists: false,
      email: 'new.operator@example.com',
      user: { id: 9 },
    });

    renderSignupPage();

    await screen.findByLabelText('Email*');
    await userEvent.type(screen.getByLabelText('Password*'), 'a very Long and compl1c@ted phrase');
    await userEvent.type(
      screen.getByLabelText('Confirm new password*'),
      'a very Long and compl1c@ted phrase',
    );
    await userEvent.click(
      screen.getByLabelText(
        'If you are willing to be contacted as part of user research, please tick this box.*',
      ),
    );
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/signup/', {
        email: 'new.operator@example.com',
        password1: 'a very Long and compl1c@ted phrase',
        password2: 'a very Long and compl1c@ted phrase',
        opt_in_user_research: true,
      });
    });
    expect(mockGoHome).toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('renders the agent organisation field and includes it in the payload', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      mode: 'agent',
      email: 'new.agent@example.com',
      organisationName: 'Acme Buses',
    });
    (api.post as jest.Mock).mockResolvedValue({
      account_exists: false,
      email: 'new.agent@example.com',
      user: { id: 10 },
    });

    renderSignupPage();

    await screen.findByLabelText('Organisation*');
    await userEvent.type(screen.getByLabelText('Organisation*'), 'Coach Consultants');
    await userEvent.type(screen.getByLabelText('Password*'), 'a very Long and compl1c@ted phrase');
    await userEvent.type(
      screen.getByLabelText('Confirm new password*'),
      'a very Long and compl1c@ted phrase',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/signup/', {
        email: 'new.agent@example.com',
        agent_organisation: 'Coach Consultants',
        password1: 'a very Long and compl1c@ted phrase',
        password2: 'a very Long and compl1c@ted phrase',
        opt_in_user_research: false,
      });
    });
  });
});
