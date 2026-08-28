/**
 * Signup Page
 *
 * Self-service registration for data consumers, mirroring Django's
 * DeveloperSignupForm. Operators and agents cannot register here: their account
 * type and organisation come from an invitation.
 *
 * IDs preserved for automated tests:
 * - id="email"
 * - id="password1"
 * - id="password2"
 * - id="error-summary-title"
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { wwwPath } from '@/config/client';
import { ensureCsrfToken } from '@/lib/api-client';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { rememberVerificationEmail } from '@/lib/auth/verification-email';

const INTENDED_USE_OPTIONS = [
  { value: '1', label: 'App' },
  { value: '2', label: 'Research' },
  { value: '3', label: 'Digital Signage' },
  { value: '4', label: 'Website / Portal' },
  { value: '5', label: 'Local Transport Authority' },
  { value: '6', label: 'Personal interests or other' },
];

const NATIONAL_INTEREST_OPTIONS = [
  { value: 'True', label: 'National' },
  { value: 'False', label: 'Regional, please provide specific location(s) if you can' },
];

const YES_NO_OPTIONS = [
  { value: 'True', label: 'Yes' },
  { value: 'False', label: 'No' },
];

const DESCRIPTION_MAX_LENGTH = 400;

const initialFormData = {
  first_name: '',
  last_name: '',
  dev_organisation: '',
  intended_use: '',
  description: '',
  national_interest: '',
  regional_areas: '',
  share_app_usage: '',
  opt_in_user_research: '',
  email: '',
  password1: '',
  password2: '',
};

type FormData = typeof initialFormData;
type FormErrors = Partial<Record<keyof FormData | 'form', string>>;

interface SignupResponse {
  account_exists?: boolean;
  email?: string;
  error?: string;
  field_errors?: Record<string, string[]>;
}

function firstErrors(fieldErrors: Record<string, string[]>): FormErrors {
  const errors: FormErrors = {};

  for (const [field, messages] of Object.entries(fieldErrors)) {
    const message = messages[0];
    if (!message) {
      continue;
    }

    if (field in initialFormData) {
      errors[field as keyof FormData] = message;
    } else {
      errors.form = message;
    }
  }

  return errors;
}

export default function SignupPage() {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<FormErrors>({});
  const [accountExists, setAccountExists] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const area = useBodsArea();

  const update = (field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/signup/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': await ensureCsrfToken() },
        body: JSON.stringify(formData),
      });
      const data: SignupResponse = await response.json().catch(() => ({}));

      if (!response.ok) {
        setErrors(
          data.field_errors
            ? firstErrors(data.field_errors)
            : { form: data.error || 'Unable to create this account.' }
        );
        setIsSubmitting(false);
        return;
      }

      if (data.account_exists) {
        setAccountExists(true);
        setIsSubmitting(false);
        return;
      }

      rememberVerificationEmail(formData.email);
      router.push('/account/confirm-email');
    } catch {
      setErrors({ form: 'Unable to create this account.' });
      setIsSubmitting(false);
    }
  };

  const summaryErrors = Object.values(errors).filter(Boolean) as string[];

  const radioGroup = (
    field: keyof FormData,
    legend: string,
    options: { value: string; label: string }[],
    hint?: string
  ) => {
    const error = errors[field];
    const hintId = hint ? `${field}-hint` : undefined;

    return (
      <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
        <fieldset className="govuk-fieldset" aria-describedby={hintId}>
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">{legend}</legend>
          {hint && (
            <div className="govuk-hint" id={hintId}>
              {hint}
            </div>
          )}
          {error && (
            <p className="govuk-error-message">
              <span className="govuk-visually-hidden">Error:</span> {error}
            </p>
          )}
          <div className="govuk-radios">
            {options.map((option) => (
              <div className="govuk-radios__item" key={option.value}>
                <input
                  className="govuk-radios__input"
                  id={`${field}-${option.value}`}
                  name={field}
                  type="radio"
                  value={option.value}
                  checked={formData[field] === option.value}
                  onChange={update(field)}
                />
                <label className="govuk-label govuk-radios__label" htmlFor={`${field}-${option.value}`}>
                  {option.label}
                </label>
              </div>
            ))}
          </div>
        </fieldset>
      </div>
    );
  };

  const textInput = (
    field: keyof FormData,
    label: string,
    options: { hint?: string; type?: string; autoComplete?: string } = {}
  ) => {
    const error = errors[field];
    const hintId = options.hint ? `${field}-hint` : undefined;

    return (
      <div className={`govuk-form-group ${error ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor={field}>
          {label}
        </label>
        {options.hint && (
          <div className="govuk-hint" id={hintId}>
            {options.hint}
          </div>
        )}
        {error && (
          <p className="govuk-error-message">
            <span className="govuk-visually-hidden">Error:</span> {error}
          </p>
        )}
        <input
          className={`govuk-input govuk-!-width-three-quarters ${error ? 'govuk-input--error' : ''}`}
          id={field}
          name={field}
          type={options.type || 'text'}
          value={formData[field]}
          onChange={update(field)}
          aria-describedby={hintId}
          autoComplete={options.autoComplete}
        />
      </div>
    );
  };

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          area,
          { label: 'Sign in', href: '/account/login' },
          { label: 'Create account', current: true }
        )}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Create account</h1>

            {accountExists ? (
              <>
                <p className="govuk-body-m">
                  An account with this email address has already been registered on BODS. Please
                  click below to sign in.
                </p>
                <p className="govuk-body-m govuk-!-margin-bottom-6">
                  If there are any further issues, please contact the BODS help desk.
                </p>
                <Link href="/account/login" className="govuk-button" data-module="govuk-button">
                  Sign in
                </Link>
              </>
            ) : (
              <>
                <p className="govuk-body-m">
                  Enter your details to create an account and start using bus open data.
                </p>

                {summaryErrors.length > 0 && <ErrorSummary errors={summaryErrors} />}

                <form onSubmit={handleSubmit} noValidate>
                  {textInput('first_name', 'First Name', { autoComplete: 'given-name' })}
                  {textInput('last_name', 'Last Name', { autoComplete: 'family-name' })}
                  {textInput('dev_organisation', 'Organisation', {
                    hint: 'If you do not belong to an organisation, please type N/A',
                    autoComplete: 'organization',
                  })}

                  {radioGroup(
                    'intended_use',
                    'What best describes your intended use?',
                    INTENDED_USE_OPTIONS,
                    'To help us to continuously improve the service, please provide details about your intended use of the data.'
                  )}

                  <div
                    className={`govuk-form-group ${
                      errors.description ? 'govuk-form-group--error' : ''
                    }`}
                  >
                    <label className="govuk-label" htmlFor="description">
                      Please provide a short description about your intended use below.
                    </label>
                    <div className="govuk-hint" id="description-hint">
                      What does your product/service do? Who is it for?
                    </div>
                    {errors.description && (
                      <p className="govuk-error-message">
                        <span className="govuk-visually-hidden">Error:</span> {errors.description}
                      </p>
                    )}
                    <textarea
                      className={`govuk-textarea ${
                        errors.description ? 'govuk-textarea--error' : ''
                      }`}
                      id="description"
                      name="description"
                      rows={3}
                      maxLength={DESCRIPTION_MAX_LENGTH}
                      value={formData.description}
                      onChange={update('description')}
                      aria-describedby="description-hint"
                    />
                  </div>

                  {radioGroup(
                    'national_interest',
                    'Which areas of data are you interested in?',
                    NATIONAL_INTEREST_OPTIONS
                  )}
                  {textInput('regional_areas', 'Regional Areas')}

                  {radioGroup(
                    'share_app_usage',
                    'Are you happy for DfT to contact you to discuss how you’re using the data?',
                    YES_NO_OPTIONS,
                    'This helps us to continuously improve the BODS service and make it usable for consumers like yourself'
                  )}
                  {radioGroup(
                    'opt_in_user_research',
                    'Would you like to be involved in the development of BODS and be contacted as part of our user research?',
                    YES_NO_OPTIONS,
                    'This helps us to continuously improve the BODS service and make it usable for consumers like yourself'
                  )}

                  {textInput('email', 'Email', { type: 'email', autoComplete: 'email' })}
                  {textInput('password1', 'Password', {
                    type: 'password',
                    hint: 'Your password should be at least 8 characters long.',
                    autoComplete: 'new-password',
                  })}
                  {textInput('password2', 'Confirm new password', {
                    type: 'password',
                    autoComplete: 'new-password',
                  })}

                  <p className="govuk-body">
                    By using this website, you consent to our{' '}
                    <a className="govuk-link" href={wwwPath('/privacy-policy')}>
                      Privacy
                    </a>{' '}
                    and{' '}
                    <a className="govuk-link" href={wwwPath('/cookie')}>
                      Cookies
                    </a>{' '}
                    policies.
                  </p>

                  <button
                    type="submit"
                    className="govuk-button"
                    data-module="govuk-button"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Creating account...' : 'Create account'}
                  </button>
                </form>
              </>
            )}
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Already have an account?</h2>
            <ul className="govuk-list">
              <li>
                <Link href="/account/login" className="govuk-link">
                  Sign in
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
