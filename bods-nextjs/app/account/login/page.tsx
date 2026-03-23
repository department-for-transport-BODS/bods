'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';
import { ErrorSummary } from '@/components/shared';
import { config } from '@/config';

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
      <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href={`HOSTS.root`}>
              Bus Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/">
              Publish Bus Open Data
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            Sign in
          </li>
        </ol>
      </nav>

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
