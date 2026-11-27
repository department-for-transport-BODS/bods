/**
 * Redirects to consumer activity stats, matching Django's RedirectDataActivityView
 * (destination logic lives in GuideMeRedirect).
 */

import { GuideMeRedirect } from '../_components/GuideMeRedirect';

export const metadata = { title: 'Guide me' };

export default function GuideMeActivityRedirectPage() {
  return <GuideMeRedirect target="activity" />;
}
