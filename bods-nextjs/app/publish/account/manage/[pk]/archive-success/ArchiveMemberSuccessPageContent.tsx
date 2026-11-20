'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';

interface MemberDetail {
  id: number;
  username: string;
  isActive: boolean;
}

function ArchiveMemberSuccessContent() {
  const params = useParams();
  const { user } = useAuth();
  const userId = params.pk as string;
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';

  const [member, setMember] = useState<MemberDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
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

  const heading = member?.isActive ? 'User has been activated' : 'User has been deactivated';
  const body = member?.isActive
    ? `User ${member.username} has been activated and will have access to the Bus Open Data Service.`
    : member
      ? `User ${member.username} has been deactivated and will no longer have access to the Bus Open Data Service.`
      : '';

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}
            {!isLoading && member && (
              <>
                <h1 className="govuk-heading-xl govuk-!-margin-bottom-6">{heading}</h1>
                <p className="govuk-body-m govuk-!-margin-top-7">{body}</p>
                <Link role="button" className="govuk-button" href={manageUrl}>
                  Go back to user management
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ArchiveMemberSuccessPage() {
  return (
    <OrgAdminRoute>
      <ArchiveMemberSuccessContent />
    </OrgAdminRoute>
  );
}
