/**
 * Redirects to consumer activity stats, matching Django's RedirectDataActivityView:
 * agents -> agent dashboard (Django deep-links a "next=data-activity" param there;
 * our agent dashboard doesn't support that yet, so agents land on the dashboard itself);
 * single-org users -> their organisation's data activity page.
 */

import { GuideMeRedirect, type DestinationFor } from '../_components/GuideMeRedirect';

const destinationFor: DestinationFor = (user) => {
  if (user.is_agent_user) {
    return '/agent-dashboard';
  }

  if (user.organisation_id) {
    return `/org/${user.organisation_id}/dataset/data-activity?prev=guide-me`;
  }

  return '/org';
};

export default function GuideMeActivityRedirectPage() {
  return <GuideMeRedirect destinationFor={destinationFor} />;
}
