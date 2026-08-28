'use client';

/**
 * Change password
 *
 * Mirrors Django's account/password_change.html (allauth PasswordChangeView).
 * IDs preserved for automated tests: id_oldpassword, id_password1, id_password2.
 */

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { getCsrfToken } from '@/lib/api-client';

type FieldErrors = {
  oldpassword?: string;
  password1?: string;
  password2?: string;
  form?: string;
};

type PasswordFieldProps = {
  id: string;
  label: string;
  autoComplete: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
};

function PasswordField({ id, label, autoComplete, value, error, onChange }: PasswordFieldProps) {
  return (
    <div className={`govuk-form-group${error ? ' govuk-form-group--error' : ''}`}>
      <label className="govuk-label" htmlFor={id}>
        {label}
      </label>
      {error && (
        <p className="govuk-error-message" id={`${id}-error`}>
          <span className="govuk-visually-hidden">Error:</span> {error}
        </p>
      )}
      <input
        className={`govuk-input govuk-!-width-three-quarters${error ? ' govuk-input--error' : ''}`}
        id={id}
        name={id.replace(/^id_/, '')}
        type="password"
        value={value}
        autoComplete={autoComplete}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function firstFieldError(
  fieldErrors: Record<string, string[] | undefined>,
  field: string,
): string {
  return fieldErrors[field]?.[0] || '';
}

function ChangePasswordContent() {
  const router = useRouter();
  const settingsUrl = '/account/settings';

  const [oldpassword, setOldpassword] = useState('');
  const [password1, setPassword1] = useState('');
  const [password2, setPassword2] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/password/change/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ oldpassword, password1, password2 }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const fieldErrors = (data.field_errors || {}) as Record<string, string[] | undefined>;
        setErrors({
          oldpassword: firstFieldError(fieldErrors, 'oldpassword'),
          password1: firstFieldError(fieldErrors, 'password1'),
          password2: firstFieldError(fieldErrors, 'password2'),
          form:
            firstFieldError(fieldErrors, '__all__') ||
            (!data.field_errors ? data.error || 'Unable to change your password.' : ''),
        });
        setIsSubmitting(false);
        return;
      }

      router.push('/account/password/change/done');
      router.refresh();
    } catch {
      setErrors({ form: 'Unable to change your password.' });
      setIsSubmitting(false);
    }
  };

  const summaryErrors = [
    errors.oldpassword ? { text: errors.oldpassword, href: '#id_oldpassword' } : '',
    errors.password1 ? { text: errors.password1, href: '#id_password1' } : '',
    errors.password2 ? { text: errors.password2, href: '#id_password2' } : '',
    errors.form || '',
  ].filter(Boolean);

  return (
    <div className="govuk-width-container">
      <Link className="govuk-back-link" href={settingsUrl}>
        Back
      </Link>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-7">Change password</h1>
            <p className="govuk-body-m govuk-!-margin-bottom-0">
              Your password should be at least 8 characters long.
            </p>

            <form onSubmit={handleSubmit} noValidate className="govuk-!-margin-top-6">
              {summaryErrors.length > 0 && (
                <ErrorSummary errors={summaryErrors} summaryId="change-password-error-title" />
              )}

              <PasswordField
                id="id_oldpassword"
                label="Current password"
                autoComplete="current-password"
                value={oldpassword}
                error={errors.oldpassword}
                onChange={setOldpassword}
              />
              <PasswordField
                id="id_password1"
                label="New password"
                autoComplete="new-password"
                value={password1}
                error={errors.password1}
                onChange={setPassword1}
              />
              <PasswordField
                id="id_password2"
                label="Confirm new password"
                autoComplete="new-password"
                value={password2}
                error={errors.password2}
                onChange={setPassword2}
              />

              <div className="govuk-button-group">
                <button
                  type="submit"
                  className="govuk-button"
                  data-module="govuk-button"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Saving...' : 'Reset password'}
                </button>
                <Link href={settingsUrl} className="govuk-button govuk-button--secondary">
                  Cancel
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChangePasswordPage() {
  return (
    <ProtectedRoute>
      <ChangePasswordContent />
    </ProtectedRoute>
  );
}
