/**
 * Redirects to the "start publishing" flow, matching Django's RedirectPublishView
 * (destination logic lives in GuideMeRedirect).
 */

import { GuideMeRedirect } from '../_components/GuideMeRedirect';

export const metadata = { title: 'Guide me' };

export default function GuideMePublishRedirectPage() {
  return <GuideMeRedirect target="publish" />;
}
