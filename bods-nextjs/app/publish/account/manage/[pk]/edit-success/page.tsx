'use client';

/**
 * Member details updated.
 *
 * Mirrors Django's users/users_manage_edit_success.html (UserEditSuccessView).
 * `pk` is the member user id.
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { api } from '@/lib/api-client';

interface MemberDetail {
  id: number;
  username: string;
}

function EditMemberSuccessContent() {
  const params = useParams();
  const userId = params.pk as string;
  const detailUrl = `/account/manage/${userId}/detail`;

  const [username, setUsername] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<MemberDetail>(`/api/publish/organisation/members/${userId}/`)
      .then((data) => {
        if (!isCancelled) setUsername(data.username);
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

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}
            {!isLoading && username && (
              <>
                <h1 className="govuk-heading-xl govuk-!-margin-bottom-6">
                  User detail has been updated
                </h1>
                <p className="govuk-body-m govuk-!-margin-top-7">
                  User {username} has been updated.
                </p>
                <Link role="button" className="govuk-button" href={detailUrl}>
                  Go back to user profile
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function EditMemberSuccessPage() {
  return (
    <OrgAdminRoute>
      <EditMemberSuccessContent />
    </OrgAdminRoute>
  );
}
