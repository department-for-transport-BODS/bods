import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { api } from '@/lib/api-client';
import { AuthError } from '@/lib/auth/session-auth';
import { HostProvider } from '@/lib/bods-host-context';
import { LOGIN_ERRORS } from '@/lib/validation/messages';
import LoginPage from './page';

const mockPush = jest.fn();
const mockLogin = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, refresh: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
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

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ login: mockLogin }),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

function renderPage() {
  return render(
    <HostProvider hostname="data.xyz.com">
      <LoginPage />
    </HostProvider>,
  );
}

describe('Login page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLogin.mockReset();
    (api.get as jest.Mock).mockResolvedValue({ verifiedEmail: null });
  });

  it('shows the Django confirmed-email copy when the session has a verified address', async () => {
    (api.get as jest.Mock).mockResolvedValue({ verifiedEmail: 'consumer@example.com' });

    renderPage();

    expect(await screen.findByRole('heading', { name: 'Email address confirmed' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.getByText('Your email address has been confirmed.')).toBeInTheDocument();
    expect(screen.getByText('You can now sign in to your account.')).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/)).toHaveValue('consumer@example.com');
  });

  it('keeps the ordinary sign-in heading when nothing was confirmed', async () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/api/auth/login/');
    });
    expect(screen.queryByText('Your email address has been confirmed.')).not.toBeInTheDocument();
  });

  it('shows Django field errors in the focused summary and above the inputs', async () => {
    renderPage();

    const form = screen.getByRole('button', { name: 'Sign In' }).closest('form');
    expect(form).toHaveAttribute('novalidate');
    fireEvent.submit(form!);

    const summary = await screen.findByRole('alert');
    expect(summary).toHaveTextContent('There is a problem');
    expect(summary).toHaveFocus();
    expect(within(summary).getByRole('link', { name: LOGIN_ERRORS.emailRequired }))
      .toHaveAttribute('href', '#id_login');
    expect(within(summary).getByRole('link', { name: LOGIN_ERRORS.passwordRequired }))
      .toHaveAttribute('href', '#id_password');

    const email = screen.getByLabelText('Email*');
    expect(email).toHaveAttribute('type', 'email');
    expect(email).toHaveAttribute('autocomplete', 'email');
    expect(email).not.toHaveAttribute('aria-describedby');
    const emailError = screen.getByText(LOGIN_ERRORS.emailRequired, {
      selector: 'span.govuk-error-message',
    });
    expect(email.closest('.govuk-form-group')).toHaveClass('govuk-form-group--error');
    expect(email).toHaveClass('govuk-input--error');
    expect(
      emailError.compareDocumentPosition(email) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    const password = screen.getByLabelText('Password*');
    const passwordError = screen.getByText(LOGIN_ERRORS.passwordRequired, {
      selector: 'span.govuk-error-message',
    });
    expect(password.closest('.govuk-form-group')).toHaveClass('govuk-form-group--error');
    expect(password).toHaveClass('govuk-input--error');
    expect(password).toHaveAttribute('aria-describedby', 'id_password-hint');
    expect(
      passwordError.compareDocumentPosition(password) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText('Your password should be at least 8 characters long.'))
      .toHaveAttribute('id', 'id_password-hint');
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('shows only the password error when only the password is missing', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('Email*'), {
      target: { value: 'person@example.com' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);

    expect(await screen.findByText(LOGIN_ERRORS.passwordRequired, {
      selector: 'span.govuk-error-message',
    })).toBeInTheDocument();
    expect(screen.queryByText(LOGIN_ERRORS.emailRequired, {
      selector: 'span.govuk-error-message',
    })).not.toBeInTheDocument();
  });

  it('shows only the email error when only the email is missing', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('Password*'), {
      target: { value: 'password' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);

    expect(await screen.findByText(LOGIN_ERRORS.emailRequired, {
      selector: 'span.govuk-error-message',
    })).toBeInTheDocument();
    expect(screen.queryByText(LOGIN_ERRORS.passwordRequired, {
      selector: 'span.govuk-error-message',
    })).not.toBeInTheDocument();
  });

  it('uses the exact Django malformed-email message without a browser tooltip', async () => {
    renderPage();
    const email = screen.getByLabelText('Email*');
    fireEvent.change(email, { target: { value: 'not-an-email' } });
    fireEvent.change(screen.getByLabelText('Password*'), {
      target: { value: 'password' },
    });
    fireEvent.submit(email.closest('form')!);

    expect(await screen.findByText(LOGIN_ERRORS.emailInvalid, {
      selector: 'span.govuk-error-message',
    })).toBeInTheDocument();
    expect(email.closest('form')).toHaveAttribute('novalidate');
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('shows the exact Django invalid-credentials message in one summary', async () => {
    mockLogin.mockRejectedValueOnce(new Error(LOGIN_ERRORS.invalidCredentials));
    renderPage();
    fireEvent.change(screen.getByLabelText('Email*'), {
      target: { value: 'person@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password*'), {
      target: { value: 'wrong-password' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);

    const summary = await screen.findByRole('alert');
    expect(within(summary).getByRole('link', { name: LOGIN_ERRORS.invalidCredentials }))
      .toHaveAttribute('href', '#');
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(summary).toHaveFocus();
  });

  it('shows the exact Django unverified-email message', async () => {
    const email = 'person@example.com';
    const message = LOGIN_ERRORS.unverifiedEmail(email);
    mockLogin.mockRejectedValueOnce(new Error(message));
    renderPage();
    fireEvent.change(screen.getByLabelText('Email*'), { target: { value: email } });
    fireEvent.change(screen.getByLabelText('Password*'), {
      target: { value: 'correct-password' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);

    expect(await screen.findByRole('link', { name: message })).toBeInTheDocument();
  });

  it('routes inactive accounts to the Django account-inactive page', async () => {
    mockLogin.mockRejectedValueOnce(
      new AuthError('Your account is inactive.', 403, 'account_inactive'),
    );
    renderPage();
    fireEvent.change(screen.getByLabelText('Email*'), {
      target: { value: 'person@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password*'), {
      target: { value: 'correct-password' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/account/inactive/');
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows the Django throttle message and a network failure without mislabelling credentials', async () => {
    mockLogin.mockRejectedValueOnce(new Error(LOGIN_ERRORS.tooManyAttempts));
    renderPage();
    fireEvent.change(screen.getByLabelText('Email*'), {
      target: { value: 'person@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password*'), {
      target: { value: 'password' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);
    expect(await screen.findByRole('link', { name: LOGIN_ERRORS.tooManyAttempts }))
      .toBeInTheDocument();

    mockLogin.mockRejectedValueOnce(new Error('Network request failed'));
    fireEvent.change(screen.getByLabelText('Email*'), {
      target: { value: 'another@example.com' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!);
    expect(await screen.findByRole('link', { name: 'Network request failed' }))
      .toBeInTheDocument();
  });
});
