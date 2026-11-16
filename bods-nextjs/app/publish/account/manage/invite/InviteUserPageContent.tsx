'use client';

/**
 * Invite a new organisation member (admin, standard, or agent).
 *
 * Django's users:invite has no org id in the URL; the organisation is taken
 * from the signed-in admin.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { api, ApiError } from '@/lib/api-client';
import { rememberInviteEmail } from '@/lib/auth/invite-email';
import { errorSummaryItems } from '@/lib/form-errors';

type AccountTypeOption = 'admin' | 'staff' | 'agent';

const FIELD_ANCHORS = {
  email: '#email',
  accountType: '#account-type-admin',
};

function InviteUser() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const orgId = user?.organisation_id;
  const canInvite = Boolean(user?.is_org_admin && orgId);
  const manageUrl = orgId ? `/account/manage/${orgId}` : '/account';

  const [email, setEmail] = useState('');
  const [accountType, setAccountType] = useState<AccountTypeOption | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isAuthLoading || canInvite) {
      return;
    }

    router.replace('/account');
  }, [isAuthLoading, canInvite, router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});

    if (!canInvite) {
      setErrors({ form: 'Unable to send this invitation.' });
      return;
    }

    if (!accountType) {
      setErrors({ accountType: 'Choose the account type' });
      return;
    }

    setIsSubmitting(true);

    try {
      await api.post(`/api/publish/organisation/${orgId}/invite/`, { email, accountType });

      rememberInviteEmail(email);
      router.push('/account/manage/invite/success');
      router.refresh();
    } catch (error) {
      setErrors(
        error instanceof ApiError && error.hasFieldErrors
          ? error.firstFieldErrors()
          : { form: 'Unable to send this invitation.' },
      );
      setIsSubmitting(false);
    }
  };

  const summaryErrors = errorSummaryItems(errors, FIELD_ANCHORS);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'User management', href: manageUrl },
            { label: 'Invite a new user', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Invite a new user</h1>
            <p className="govuk-body-m"> Send an email invite to a new user so they can publish and update data sets </p>
            {isAuthLoading && <p className="govuk-body">Loading...</p>}

            {!isAuthLoading && canInvite && (
              <form onSubmit={handleSubmit} noValidate>
                {summaryErrors.length > 0 && (
                  <ErrorSummary errors={summaryErrors} summaryId="invite-user-error-title" />
                )}
                <div className={`govuk-form-group ${errors.email ? 'govuk-form-group--error' : ''}`}>
                  <label className="govuk-label" htmlFor="email">Email</label>
                  {errors.email && (
                    <p className="govuk-error-message" id="email-error">
                      <span className="govuk-visually-hidden">Error:</span> {errors.email}
                    </p>
                  )}
                  <input
                    className={`govuk-input ${errors.email ? 'govuk-input--error' : ''}`}
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    aria-describedby={errors.email ? 'email-error' : undefined}
                    required
                  />
                </div>

                <fieldset className="govuk-fieldset">
                  <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">
                    Choose the account type
                  </legend>
                  {errors.accountType && (
                    <p className="govuk-error-message">
                      <span className="govuk-visually-hidden">Error:</span> {errors.accountType}
                    </p>
                  )}
                  <div className="govuk-radios">
                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="account-type-admin"
                        type="radio"
                        name="account_type"
                        checked={accountType === 'admin'}
                        onChange={() => setAccountType('admin')}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="account-type-admin">
                        Admin - key account holders of the organisation
                      </label>
                    </div>
                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="account-type-staff"
                        type="radio"
                        name="account_type"
                        checked={accountType === 'staff'}
                        onChange={() => setAccountType('staff')}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="account-type-staff">
                        Standard - staff of the organisation
                      </label>
                    </div>
                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="account-type-agent"
                        type="radio"
                        name="account_type"
                        checked={accountType === 'agent'}
                        onChange={() => setAccountType('agent')}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="account-type-agent">
                        Agent - agents acting on behalf of the organisation
                      </label>
                    </div>
                  </div>
                </fieldset>

                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button" disabled={isSubmitting}>
                    {isSubmitting ? 'Sending...' : 'Send invitation'}
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(manageUrl)}>
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function InviteUserPage() {
  return (
    <OrgAdminRoute>
      <InviteUser />
    </OrgAdminRoute>
  );
}
