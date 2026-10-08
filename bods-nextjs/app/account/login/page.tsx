'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { resolvePostLoginRedirect } from '@/lib/auth/post-login-redirect';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [verifiedEmail, setVerifiedEmail] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{        // used to identify field validation errors - different from the above error for API authentication errors
    email?: string;
    password?: string;
  }>({});
  const [isSummaryHighlighted, setIsSummaryHighlighted] = useState(false);
  const summaryRef = useRef<HTMLDivElement>(null);
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const area = useBodsArea();

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
    if (!isSummaryHighlighted) return;
    summaryRef.current?.focus();
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
  }, [isSummaryHighlighted]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setIsSummaryHighlighted(true);
    const emailInput =  e.currentTarget.elements.namedItem('email') as HTMLInputElement;
    const nextFieldErrors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      nextFieldErrors.email = 'Please provide an email';
    }
    else if (emailInput.validity.typeMismatch) {
      nextFieldErrors.email = 'Enter an email address in the right format, like name@example.com';
    }
    if (!password) {
      nextFieldErrors.password = 'Please provide a password';
    }

    setFieldErrors(nextFieldErrors);

    if (Object.keys(nextFieldErrors).length > 0){
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
      setError(err instanceof Error ? err.message : 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <Breadcrumbs items={hostBreadcrumbs(area, { label: 'Sign in', current: true })} />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Sign in</h1>

            {(error || fieldErrors.email || fieldErrors.password) && (
              <div
                ref={summaryRef}
                tabIndex={-1}
                className={`govuk-error-summary ${
                  isSummaryHighlighted ? 'app-error-summary--highlighted' : ''
                }`}
                aria-labelledby="error-summary-title"
                role="alert"
              >
                <h2 className="govuk-error-summary__title" id="error-summary-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    {fieldErrors.email && (
                      <li>
                        <a className="govuk-link" href="#email">
                          {fieldErrors.email}
                        </a>
                      </li>
                    )}
                    {fieldErrors.password && (
                      <li>
                        <a className="govuk-link" href="#password">
                          {fieldErrors.password}
                        </a>
                      </li>
                    )}
                    {error && <li>{error}</li>}
                  </ul>
                </div>
              </div>
            )}
            <h1 className="govuk-heading-xl">
              {verifiedEmail ? 'Email address confirmed' : 'Sign in'}
            </h1>

            {verifiedEmail && (
              <>
                <p className="govuk-body">Your email address has been confirmed.</p>
                <p className="govuk-body">You can now sign in to your account.</p>
              </>
            )}

            {error && <ErrorSummary errors={[error]} />}

            <form onSubmit={handleSubmit} noValidate>
              <div className={`govuk-form-group ${fieldErrors.email ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="email">
                  Email<span className="govuk-visually-hidden"> (required)</span>*
                </label>
                <input
                  className={`govuk-input ${fieldErrors.email ? 'govuk-input--error' : ''}`}
                  id="email"
                  name="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  aria-invalid={Boolean(fieldErrors.email)}
                  aria-describedby={fieldErrors.email ? 'email-error' : undefined}
                />
                {fieldErrors.email && (
                  <p className="govuk-error-message" id="email-error">
                    {fieldErrors.email}
                  </p>
                )}
              </div>

              <div className={`govuk-form-group ${fieldErrors.password ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="password">
                  Password<span className="govuk-visually-hidden"> (required)</span>*
                </label>
                <input
                  className={`govuk-input ${fieldErrors.password ? 'govuk-input--error' : ''}`}
                  id="password"
                  name="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  aria-invalid={Boolean(fieldErrors.password)}
                  aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                />
                {fieldErrors.password && (
                  <p className="govuk-error-message" id="password-error">
                    {fieldErrors.password}
                  </p>
                )}
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
