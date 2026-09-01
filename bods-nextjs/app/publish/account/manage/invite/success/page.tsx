'use client';

/**
 * Invitation sent.
 *
 * Mirrors Django's users/users_invite_added.html (InviteSuccessView).
 */

import { useSyncExternalStore } from 'react';
import Link from 'next/link';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { useAuth } from '@/hooks/useAuth';
import {
  inviteEmailServerSnapshot,
  readInviteEmail,
  subscribeToInviteEmail,
} from '@/lib/auth/invite-email';

function InviteSuccessContent() {
  const { user } = useAuth();
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';
  const inviteEmail = useSyncExternalStore(
    subscribeToInviteEmail,
    readInviteEmail,
    inviteEmailServerSnapshot,
  );

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-6">Invitation has been sent</h1>
            <p className="govuk-body-m govuk-!-margin-top-7">
              An email invite has been sent
              {inviteEmail ? ` to ${inviteEmail}.` : '.'} You will be notified when they accept your
              invitation.
            </p>
            <p className="govuk-body-m govuk-!-margin-top-7">
              Please note that even if you nominate an agent, it is still your legal obligation to
              ensure that your data is up to date. It is recommended you have consistent
              communication with your agent and have contracts agreed with them external to this
              platform.
            </p>
            <Link role="button" className="govuk-button" href={manageUrl}>
              Go back to user management
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function InviteSuccessPage() {
  return (
    <OrgAdminRoute>
      <InviteSuccessContent />
    </OrgAdminRoute>
  );
}
