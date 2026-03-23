/**
 * Signup Page
 * 
 * User registration page with role selection
 * 
 * IDs preserved for automated tests:
 * - id="email"
 * - id="role"
 * - id="password1"
 * - id="password2"
 * - id="error-summary-title"
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import Link from 'next/link';
import { ErrorSummary } from '@/components/shared';

export default function SignupPage() {
  const [formData, setFormData] = useState({
    email: '',
    password1: '',
    password2: '',
    role: 'developer' as 'developer' | 'operator' | 'agent',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password1 !== formData.password2) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await api.post('/api/auth/signup/', {
        email: formData.email,
        password: formData.password1,
        role: formData.role,
      });

      router.push('/account/login?registered=true');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Create an account</h1>

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
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  autoComplete="email"
                />
              </div>

              <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="role">
                  Account type
                </label>
                <select
                  className="govuk-select"
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as typeof formData.role })}
                  required
                >
                  <option value="developer">Developer</option>
                  <option value="operator">Operator</option>
                  <option value="agent">Agent</option>
                </select>
              </div>

              <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="password1">
                  Password
                </label>
                <input
                  className={`govuk-input ${error ? 'govuk-input--error' : ''}`}
                  id="password1"
                  name="password1"
                  type="password"
                  value={formData.password1}
                  onChange={(e) => setFormData({ ...formData, password1: e.target.value })}
                  required
                  autoComplete="new-password"
                />
              </div>

              <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="password2">
                  Confirm password
                </label>
                <input
                  className={`govuk-input ${error ? 'govuk-input--error' : ''}`}
                  id="password2"
                  name="password2"
                  type="password"
                  value={formData.password2}
                  onChange={(e) => setFormData({ ...formData, password2: e.target.value })}
                  required
                  autoComplete="new-password"
                />
              </div>

              <button
                type="submit"
                className="govuk-button"
                data-module="govuk-button"
                disabled={isLoading}
              >
                {isLoading ? 'Creating account...' : 'Create account'}
              </button>
            </form>

            <p className="govuk-body">
              Already have an account?{' '}
              <Link href="/account/login" className="govuk-link">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

