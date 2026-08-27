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
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { getCsrfToken } from '@/lib/api-client';

type AccountTypeOption = 'admin' | 'staff' | 'agent';

function InviteUser() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const orgId = user?.organisation_id;
  const manageUrl = orgId ? `/publish/account/manage/${orgId}` : '/publish/account';

  const [email, setEmail] = useState('');
  const [accountType, setAccountType] = useState<AccountTypeOption | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isAuthLoading) return;
    if (!orgId) {
      router.replace('/publish/account');
    }
  }, [isAuthLoading, orgId, router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});

    if (!orgId) {
      setErrors({ form: 'Unable to send this invitation.' });
      return;
    }

    if (!accountType) {
      setErrors({ accountType: 'Choose the account type' });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`/api/publish/organisation/${orgId}/invite/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ email, accountType }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const fieldErrors = data.field_errors || {};
        setErrors({
          email: fieldErrors.email?.[0],
          accountType: fieldErrors.accountType?.[0],
          form: !data.field_errors ? data.error || 'Unable to send this invitation.' : '',
        });
        setIsSubmitting(false);
        return;
      }

      router.push(manageUrl);
      router.refresh();
    } catch {
      setErrors({ form: 'Unable to send this invitation.' });
      setIsSubmitting(false);
    }
  };

  const summaryErrors = Object.values(errors).filter(Boolean) as string[];

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

            {isAuthLoading && <p className="govuk-body">Loading...</p>}

            {!isAuthLoading && orgId && (
              <form onSubmit={handleSubmit} noValidate>
                {summaryErrors.length > 0 && (
                  <ErrorSummary errors={summaryErrors} summaryId="invite-user-error-title" />
                )}

                <div className="govuk-form-group">
                  <label className="govuk-label" htmlFor="email">Email</label>
                  <input
                    className="govuk-input"
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <fieldset className="govuk-fieldset">
                  <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">
                    Choose the account type
                  </legend>
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
    <ProtectedRoute>
      <InviteUser />
    </ProtectedRoute>
  );
}
