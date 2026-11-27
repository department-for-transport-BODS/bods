/**
 * Redirects to the organisation profile page, matching Django's RedirectProfileView
 * (destination logic lives in GuideMeRedirect).
 */

import { GuideMeRedirect } from '../_components/GuideMeRedirect';

export const metadata = { title: 'Guide me' };

export default function GuideMeProfileRedirectPage() {
  return <GuideMeRedirect target="profile" />;
}
