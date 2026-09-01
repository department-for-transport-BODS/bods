/**
 * Redirects to the "start publishing" flow, matching Django's RedirectPublishView:
 * agents -> select organisation; single-org users -> choose data type.
 */

import { GuideMeRedirect, type DestinationFor } from '../_components/GuideMeRedirect';

const destinationFor: DestinationFor = (user) => {
  if (!user.is_agent_user && user.organisation_id) {
    return `/org/${user.organisation_id}/dataset`;
  }

  return '/org';
};

export default function GuideMePublishRedirectPage() {
  return <GuideMeRedirect destinationFor={destinationFor} />;
}
