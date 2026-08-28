/**
 * Redirects to the publisher dashboard, matching Django's RedirectDashBoardView:
 * agents -> agent dashboard; single-org users -> their timetable list (feed-list default).
 */

import { GuideMeRedirect, type DestinationFor } from '../_components/GuideMeRedirect';

const destinationFor: DestinationFor = (user) => {
  if (user.is_agent_user) {
    return '/agent-dashboard';
  }

  if (user.organisation_id) {
    return `/org/${user.organisation_id}/dataset/timetable`;
  }

  return '/org';
};

export default function GuideMeDashboardRedirectPage() {
  return <GuideMeRedirect destinationFor={destinationFor} />;
}
