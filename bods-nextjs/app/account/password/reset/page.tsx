/**
 * Password Reset Page
 * 
 * Allows users to request a password reset
 * 
 * IDs preserved for automated tests:
 * - id="email"
 * - id="error-summary-title"
 */

'use client';

import { useState } from 'react';
import { api } from '@/lib/api-client';
import Link from 'next/link';
import { ErrorSummary } from '@/components/shared';

export default function PasswordResetPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await api.post('/api/auth/password/reset/', { email });
      setSubmitted(true);
    } catch {
      setError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Check your email</h1>
              <p className="govuk-body">
                  If an account exists with that email address, we've sent you a password reset link.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Reset your password</h1>

            {error && <ErrorSummary errors={[error]} />}

            <form onSubmit={handleSubmit}>
              <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="email">
                  Email address
                </label>
                <input
                  className={`govuk-input ${error ? 'govuk-input--error' : ''}`}
                  id="email"
                  name="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <button
                type="submit"
                className="govuk-button"
                data-module="govuk-button"
                disabled={isLoading}
              >
                {isLoading ? 'Sending...' : 'Send reset link'}
              </button>
            </form>

            <p className="govuk-body">
              <Link href="/account/login" className="govuk-link">
                Back to sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

