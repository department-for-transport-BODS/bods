/**
 * Redirects to the organisation profile page, matching Django's RedirectProfileView.
 */

import { GuideMeRedirect, type DestinationFor } from '../_components/GuideMeRedirect';

const destinationFor: DestinationFor = (user) =>
  user.organisation_id ? `/account/manage/org-profile/${user.organisation_id}` : '/account';

export default function GuideMeProfileRedirectPage() {
  return <GuideMeRedirect destinationFor={destinationFor} />;
}
