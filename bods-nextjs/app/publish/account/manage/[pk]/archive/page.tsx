'use client';

/**
 * Deactivate or reactivate a member's account (toggle is_active).
 * Django used this view for both `/archive/` and `/activate/`.
 * `pk` is the member user id.
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

interface MemberDetail {
  id: number;
  username: string;
  isActive: boolean;
}

function ArchiveMember() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const area = useBodsArea();
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
    if (!member) {
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      // Send the state we are moving to, not a toggle, so a stale page cannot
      // flip the member the wrong way.
      await api.post(`/api/publish/organisation/members/${userId}/set-active/`, {
        isActive: !member.isActive,
      });

      router.push(`/account/manage/${userId}/archive-success`);
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
          items={hostBreadcrumbs(
            area,
            { label: 'User management', href: manageUrl },
            { label: 'Deactivate/reactivate', current: true },
          )}
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
    <OrgAdminRoute>
      <ArchiveMember />
    </OrgAdminRoute>
  );
}
