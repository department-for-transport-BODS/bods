/**
 * Redirects to the publisher dashboard, matching Django's RedirectDashBoardView
 * (destination logic lives in GuideMeRedirect).
 */

import { GuideMeRedirect } from '../_components/GuideMeRedirect';

export const metadata = { title: 'Guide me' };

export default function GuideMeDashboardRedirectPage() {
  return <GuideMeRedirect target="dashboard" />;
}
