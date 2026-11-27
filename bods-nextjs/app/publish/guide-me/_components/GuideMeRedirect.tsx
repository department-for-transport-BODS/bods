'use client';

/**
 * Client-side equivalent of Django's guide-me Redirect*View classes: work out a
 * destination from the signed-in user, then replace the current history entry.
 *
 * Destinations are public paths (no /publish prefix); the proxy maps them onto
 * the internal route for the publish host.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types';

export type GuideMeTarget = 'activity' | 'dashboard' | 'profile' | 'publish';


export const DESTINATIONS: Record<GuideMeTarget, (user: User) => string> = {
  // Django RedirectDataActivityView: agents -> agent dashboard (which links each
  // organisation to its data activity page); org users -> their data activity page.
  activity: (user) => {
    if (user.is_agent_user) {
      return '/agent-dashboard?next=data-activity&prev=guide-me';
    }

    if (user.organisation_id) {
      return `/org/${user.organisation_id}/dataset/data-activity?prev=guide-me`;
    }

    return '/org';
  },
  // Django RedirectDashBoardView: agents -> agent dashboard; org users -> feed-list.
  dashboard: (user) => {
    if (user.is_agent_user) {
      return '/agent-dashboard';
    }

    if (user.organisation_id) {
      return `/org/${user.organisation_id}/dataset/timetable`;
    }

    return '/org';
  },
  // Django RedirectProfileView: organisation profile.
  profile: (user) =>
    user.organisation_id ? `/account/manage/org-profile/${user.organisation_id}` : '/account',
  // Django RedirectPublishView: agents -> select organisation; org users -> select data.
  publish: (user) =>
    !user.is_agent_user && user.organisation_id ? `/org/${user.organisation_id}/dataset` : '/org',
};

function Redirect({ target }: { target: GuideMeTarget }) {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      return;
    }

    router.replace(DESTINATIONS[target](user));
  }, [user, router, target]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <p className="govuk-body">Redirecting...</p>
      </div>
    </div>
  );
}

export function GuideMeRedirect({ target }: { target: GuideMeTarget }) {
  return (
    <ProtectedRoute>
      <Redirect target={target} />
    </ProtectedRoute>
  );
}
