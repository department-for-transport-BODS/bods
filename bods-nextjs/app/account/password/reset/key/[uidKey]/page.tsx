'use client';

/**
 * Set a new password from the uidb36-key in the reset email.
 *
 * Mirrors Django's account/password_reset_from_key.html.
 * IDs preserved  id_password1, id_password2.
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api, ApiError } from '@/lib/api-client';
import { parsePasswordResetUidKey, goToPasswordResetSuccess } from '@/lib/auth/password-reset';
import { useBodsArea } from '@/lib/bods-host-context';
import { errorSummaryItems } from '@/lib/form-errors';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

type FieldErrors = {
  password1?: string;
  password2?: string;
  form?: string;
};

const FIELD_ANCHORS = {
  password1: '#id_password1',
  password2: '#id_password2',
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
        className={`govuk-input govuk-!-width-one-half${error ? ' govuk-input--error' : ''}`}
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

export default function PasswordResetFromKeyPage() {
  const params = useParams();
  const area = useBodsArea();
  const uidKey = String(params.uidKey || '');
  const parsed = parsePasswordResetUidKey(uidKey);

  const [linkState, setLinkState] = useState<'checking' | 'valid' | 'invalid'>(
    parsed ? 'checking' : 'invalid',
  );
  const [password1, setPassword1] = useState('');
  const [password2, setPassword2] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});

  useEffect(() => {
    const token = parsePasswordResetUidKey(uidKey);
    if (!token) {
      return;
    }

    let isCancelled = false;

    api
      .get<{ valid: boolean }>(
        `/api/auth/password/reset/key/?uidb36=${encodeURIComponent(token.uidb36)}&key=${encodeURIComponent(token.key)}`,
      )
      .then(() => {
        if (!isCancelled) setLinkState('valid');
      })
      .catch(() => {
        if (!isCancelled) setLinkState('invalid');
      });

    return () => {
      isCancelled = true;
    };
  }, [uidKey]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!parsed) {
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      await api.post('/api/auth/password/reset/key/', {
        uidb36: parsed.uidb36,
        key: parsed.key,
        password1,
        password2,
      });

      goToPasswordResetSuccess();
    } catch (error) {
      if (error instanceof ApiError && error.status === 400 && !error.hasFieldErrors) {
        setLinkState('invalid');
        setIsSubmitting(false);
        return;
      }

      if (error instanceof ApiError && error.hasFieldErrors) {
        const { __all__: nonFieldError, ...fields } = error.firstFieldErrors();
        setErrors({ ...fields, form: nonFieldError });
      } else {
        setErrors({ form: 'Unable to reset your password.' });
      }
      setIsSubmitting(false);
    }
  };

  const summaryErrors = errorSummaryItems(errors, FIELD_ANCHORS);

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          area,
          { label: 'Reset password', href: '/account/password/reset' },
          { label: 'Choose a new password', current: true },
        )}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Reset password</h1>

            {linkState === 'checking' && <p className="govuk-body">Checking this reset link...</p>}

            {linkState === 'invalid' && (
              <>
                <h2 className="govuk-heading-m">The link you have used is invalid</h2>
                <p className="govuk-body">
                  The password reset link was invalid, possibly because it has already been used.
                  Please request a{' '}
                  <Link className="govuk-link" href="/account/password/reset">
                    new password reset
                  </Link>
                  .
                </p>
              </>
            )}

            {linkState === 'valid' && (
              <>
                <p className="govuk-body-l">Enter your new password in the field below.</p>
                <p className="govuk-body-m">Your password should be at least 8 characters long.</p>

                <form onSubmit={handleSubmit} noValidate className="govuk-!-margin-top-6">
                  {summaryErrors.length > 0 && (
                    <ErrorSummary errors={summaryErrors} summaryId="reset-password-error-title" />
                  )}

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

                  <button
                    type="submit"
                    className="govuk-button"
                    data-module="govuk-button"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Saving...' : 'Reset password'}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
