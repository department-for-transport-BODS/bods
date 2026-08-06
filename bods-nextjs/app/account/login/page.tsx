'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { HOSTS } from '@/config/client';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      router.push('/');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Bus Open Data Service', href: HOSTS.www },
          { label: 'Publish Bus Open Data', href: '/' },
          { label: 'Sign in', current: true },
        ]}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Sign in</h1>

            {error && <ErrorSummary errors={[error]} />}

            <form onSubmit={handleSubmit}>
              <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="email">
                  Email<span className="govuk-visually-hidden"> (required)</span>*
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

              <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="password">
                  Password<span className="govuk-visually-hidden"> (required)</span>*
                </label>
                <input
                  className={`govuk-input ${error ? 'govuk-input--error' : ''}`}
                  id="password"
                  name="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
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
