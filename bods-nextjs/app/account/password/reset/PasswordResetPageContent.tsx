'use client';

/**
 * Request a password reset email.
 *
 * Mirrors Django's account/password_reset.html (PasswordResetView).
 * IDs preserved : id="email", id="error-summary-title".
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api, ApiError } from '@/lib/api-client';
import { rememberPasswordResetEmail } from '@/lib/auth/password-reset';
import { useBodsArea } from '@/lib/bods-host-context';
import { errorSummaryItems } from '@/lib/form-errors';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

export default function PasswordResetPage() {
  const router = useRouter();
  const area = useBodsArea();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});
    setIsLoading(true);

    try {
      const response = await api.post<{ email: string }>('/api/auth/password/reset/', { email });
      rememberPasswordResetEmail(response.email || email);
      router.push('/account/password/reset/done');
    } catch (error) {
      if (error instanceof ApiError && error.hasFieldErrors) {
        setErrors(error.firstFieldErrors());
      } else {
        setErrors({ form: 'Unable to send a password reset email.' });
      }
      setIsLoading(false);
    }
  };

  const summaryErrors = errorSummaryItems(errors, { email: '#email' });

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          area,
          { label: 'Sign in', href: '/account/login' },
          { label: 'Reset password', current: true },
        )}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Forgot your password?</h1>
            <p className="govuk-body">Enter your email address to reset your password.</p>

            <form onSubmit={handleSubmit} noValidate>
              {summaryErrors.length > 0 && (
                <ErrorSummary errors={summaryErrors} summaryId="error-summary-title" />
              )}

              <div className={`govuk-form-group${errors.email ? ' govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="email">
                  Email*
                </label>
                {errors.email && (
                  <p className="govuk-error-message" id="email-error">
                    <span className="govuk-visually-hidden">Error:</span> {errors.email}
                  </p>
                )}
                <input
                  className={`govuk-input govuk-!-width-three-quarters${errors.email ? ' govuk-input--error' : ''}`}
                  id="email"
                  name="email"
                  type="email"
                  value={email}
                  autoComplete="email"
                  aria-describedby={errors.email ? 'email-error' : undefined}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>

              <button type="submit" className="govuk-button" data-module="govuk-button" disabled={isLoading}>
                {isLoading ? 'Sending...' : 'Continue'}
              </button>
            </form>
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Don&apos;t have an account?</h2>
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
  );
}
