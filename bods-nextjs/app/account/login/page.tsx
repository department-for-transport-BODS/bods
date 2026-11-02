'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { AuthError } from '@/lib/auth/session-auth';
import { HOSTS } from '@/config/client';
import { useBodsArea } from '@/lib/bods-host-context';
import { resolvePostLoginRedirect } from '@/lib/auth/post-login-redirect';
import { errorSummaryItems } from '@/lib/form-errors';
import { LOGIN_ERRORS } from '@/lib/validation/messages';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [verifiedEmail, setVerifiedEmail] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string;
    password?: string;
  }>({});
  const [summaryAttempt, setSummaryAttempt] = useState(0);
  const [isSummaryHighlighted, setIsSummaryHighlighted] = useState(false);
  const summaryRef = useRef<HTMLDivElement>(null);
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const area = useBodsArea();
  const breadcrumbs = [
    { label: 'Bus Open Data Service', href: HOSTS.www },
    ...(area === 'www'
      ? [{ label: 'Bus Open Data Service', href: HOSTS.www }]
      : [
          {
            label:
              area === 'data'
                ? 'Find Open Data Service'
                : area === 'publish'
                  ? 'Publish Open Data Service'
                  : 'BODS admin home',
            href: HOSTS[area],
          },
        ]),
    { label: 'Sign in', href: '/account/login' },
  ];

  useEffect(() => {
    let isCancelled = false;

    api
      .get<{ verifiedEmail?: string | null }>('/api/auth/login/')
      .then((data) => {
        if (isCancelled || !data.verifiedEmail) {
          return;
        }

        setVerifiedEmail(data.verifiedEmail);
        setEmail(data.verifiedEmail);
      })
      .catch(() => {
        // Sign-in still works without the confirmation banner.
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!error && !fieldErrors.email && !fieldErrors.password) return;

    summaryRef.current?.focus();
    setIsSummaryHighlighted(true);
    const handleDocumentClick = (event: MouseEvent) => {
      const target = event.target;

      if (target instanceof Node && !summaryRef.current?.contains(target)) {
        setIsSummaryHighlighted(false);
      }
    };

    document.addEventListener('click', handleDocumentClick);

    return () => {
      document.removeEventListener('click', handleDocumentClick);
    };
  }, [error, fieldErrors.email, fieldErrors.password, summaryAttempt]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});
    setIsSummaryHighlighted(false);
    setSummaryAttempt((attempt) => attempt + 1);
    const emailInput = e.currentTarget.elements.namedItem('login') as HTMLInputElement;
    const nextFieldErrors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      nextFieldErrors.email = LOGIN_ERRORS.emailRequired;
    } else if (emailInput.validity.typeMismatch) {
      nextFieldErrors.email = LOGIN_ERRORS.emailInvalid;
    }
    if (!password) {
      nextFieldErrors.password = LOGIN_ERRORS.passwordRequired;
    }

    setFieldErrors(nextFieldErrors);

    if (Object.keys(nextFieldErrors).length > 0) {
      return;
    }

    setIsLoading(true);

    try {
      await login(email, password);
      const destination = resolvePostLoginRedirect(searchParams.get('next'));
      if (destination.startsWith('http://') || destination.startsWith('https://')) {
        window.location.assign(destination);
        return;
      }
      router.push(destination);
      router.refresh();
    } catch (err) {
      if (err instanceof AuthError && err.code === 'account_inactive') {
        router.push('/account/inactive/');
        return;
      }

      setError(err instanceof Error ? err.message : LOGIN_ERRORS.invalidCredentials);
    } finally {
      setIsLoading(false);
    }
  };

  const summaryErrors = [
    ...errorSummaryItems(fieldErrors, {
      email: '#id_login',
      password: '#id_password',
    }),
    ...(error
      ? [{ text: error, href: '#', className: 'govuk-error-message' }]
      : []),
  ];

  return (
    <div className="govuk-width-container">
      <Breadcrumbs items={breadcrumbs} />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">
              {verifiedEmail ? 'Email address confirmed' : 'Sign in'}
            </h1>

            {summaryErrors.length > 0 && (
              <ErrorSummary
                containerRef={summaryRef}
                tabIndex={-1}
                dataModule="govuk-error-summary"
                errors={summaryErrors}
                className={
                  isSummaryHighlighted ? 'app-error-summary--highlighted' : ''
                }
              />
            )}

            {verifiedEmail && (
              <>
                <p className="govuk-body">Your email address has been confirmed.</p>
                <p className="govuk-body">You can now sign in to your account.</p>
              </>
            )}

            <form onSubmit={handleSubmit} noValidate>
              <div className={`govuk-form-group ${fieldErrors.email ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="id_login">Email*</label>
                {fieldErrors.email && (
                  <span className="govuk-error-message" id="1_id_login-error">
                    {fieldErrors.email}
                  </span>
                )}
                <input
                  className={`govuk-!-width-three-quarters govuk-input ${fieldErrors.email ? 'govuk-input--error' : ''}`}
                  id="id_login"
                  name="login"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder=""
                  maxLength={320}
                  required
                  autoComplete="email"
                />
              </div>

              <div className={`govuk-form-group ${fieldErrors.password ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="id_password">Password*</label>
                <span id="id_password-hint" className="govuk-hint">
                  Your password should be at least 8 characters long.
                </span>
                {fieldErrors.password && (
                  <span className="govuk-error-message" id="1_id_password-error">
                    {fieldErrors.password}
                  </span>
                )}
                <input
                  className={`govuk-!-width-three-quarters govuk-input ${fieldErrors.password ? 'govuk-input--error' : ''}`}
                  id="id_password"
                  name="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder=""
                  required
                  autoComplete="current-password"
                  aria-describedby="id_password-hint"
                />
              </div>

              <button
                type="submit"
                className="govuk-button"
                data-module="govuk-button"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          </div>

          <div className="govuk-grid-column-one-third">
            <div className="govuk-!-margin-bottom-6">
              <h2 className="govuk-heading-m">Forgot your password?</h2>
              <ul className="govuk-list">
                <li>
                  <Link href="/account/password/reset" className="govuk-link">
                    Reset your password
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="govuk-heading-m">Don't have an account?</h2>
              <ul className="govuk-list">
                <li>
                  <Link href="/account/signup" className="govuk-link">
                    Create account
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
