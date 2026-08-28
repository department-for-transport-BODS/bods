'use client';

/**
 * Deactivate or reactivate a member's account (toggle is_active).
 * Django used this view for both `/archive/` and `/activate/`.
 * `pk` is the member user id.
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
  isActive: boolean;
}

function ArchiveMember() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const userId = params.pk as string;
  const detailUrl = `/account/manage/${userId}/detail`;
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';

  const [member, setMember] = useState<MemberDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<MemberDetail>(`/api/publish/organisation/members/${userId}/`)
      .then((data) => {
        if (!isCancelled) setMember(data);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load this member.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [userId]);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      const response = await fetch(`/api/publish/organisation/members/${userId}/toggle-active/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
      });

      if (!response.ok) {
        setError('Unable to update this member. Please try again.');
        setIsSubmitting(false);
        return;
      }

      router.push(detailUrl);
      router.refresh();
    } catch {
      setError('Unable to update this member. Please try again.');
      setIsSubmitting(false);
    }
  };

  const action = member?.isActive ? 'deactivate' : 'reactivate';

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'User management', href: manageUrl },
            { label: 'Deactivate/reactivate', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="archive-member-error-title" />}

            {!isLoading && member && (
              <>
                <h1 className="govuk-heading-l">
                  Are you sure you want to {action} {member.username}?
                </h1>
                <div className="govuk-button-group">
                  <button type="button" className="govuk-button" disabled={isSubmitting} onClick={handleConfirm}>
                    Confirm
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(detailUrl)}>
                    Cancel
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ArchiveMemberPage() {
  return (
    <ProtectedRoute>
      <ArchiveMember />
    </ProtectedRoute>
  );
}
