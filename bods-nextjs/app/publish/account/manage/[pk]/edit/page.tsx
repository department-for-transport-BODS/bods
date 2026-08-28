'use client';

/**
 * Edit a member's username, email, and account type (admin/standard only).
 * `pk` is the member user id (`/account/manage/<user_id>/edit/`).
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { api, getCsrfToken } from '@/lib/api-client';

interface MemberDetail {
  id: number;
  username: string;
  email: string;
  accountType: number;
}

const ORG_ADMIN = 2;
const ORG_STAFF = 3;

function EditMember() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const userId = params.pk as string;
  const detailUrl = `/account/manage/${userId}/detail`;
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [accountType, setAccountType] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    let isCancelled = false;

    api
      .get<MemberDetail>(`/api/publish/organisation/members/${userId}/`)
      .then((data) => {
        if (isCancelled) return;
        setUsername(data.username);
        setEmail(data.email);
        setAccountType(data.accountType);
      })
      .catch(() => {
        if (!isCancelled) setErrors({ form: 'Unable to load this member.' });
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [userId]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const response = await fetch(`/api/publish/organisation/members/${userId}/update/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ username, email, accountType }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const fieldErrors = data.field_errors || {};
        setErrors({
          username: fieldErrors.username?.[0],
          email: fieldErrors.email?.[0],
          accountType: fieldErrors.accountType?.[0],
          form: !data.field_errors ? data.error || 'Unable to save this member.' : '',
        });
        setIsSubmitting(false);
        return;
      }

      router.push(detailUrl);
      router.refresh();
    } catch {
      setErrors({ form: 'Unable to save this member.' });
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
            { label: 'Edit member', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Edit user</h1>

            {isLoading && <p className="govuk-body">Loading...</p>}

            {!isLoading && (
              <form onSubmit={handleSubmit} noValidate>
                {summaryErrors.length > 0 && (
                  <ErrorSummary errors={summaryErrors} summaryId="edit-member-error-title" />
                )}

                <div className="govuk-form-group">
                  <label className="govuk-label" htmlFor="username">Username</label>
                  <input
                    className="govuk-input"
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>

                <div className="govuk-form-group">
                  <label className="govuk-label" htmlFor="email">Email</label>
                  <input
                    className="govuk-input"
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                <fieldset className="govuk-fieldset">
                  <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">User type</legend>
                  <div className="govuk-radios">
                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="account-type-admin"
                        type="radio"
                        name="account_type"
                        checked={accountType === ORG_ADMIN}
                        onChange={() => setAccountType(ORG_ADMIN)}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="account-type-admin">Admin</label>
                    </div>
                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="account-type-staff"
                        type="radio"
                        name="account_type"
                        checked={accountType === ORG_STAFF}
                        onChange={() => setAccountType(ORG_STAFF)}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="account-type-staff">Standard</label>
                    </div>
                  </div>
                </fieldset>

                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : 'Save'}
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(detailUrl)}>
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

export default function EditMemberPage() {
  return (
    <ProtectedRoute>
      <EditMember />
    </ProtectedRoute>
  );
}
