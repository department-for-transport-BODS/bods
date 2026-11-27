/**
 * Phase Banner Component
 *
 * Displays the BETA phase banner at the top of the page.
 * Source: transit_odp/templates/banner.html
 * TODO: At a later date this should be replaced with an off the shelf lib component that can be shared across the estate
 */

'use client';

import { useSyncExternalStore } from 'react';
import { usePathname } from 'next/navigation';
import { wwwPath } from '@/config/client';

interface PhaseBannerProps {
  hideGlobalFeedback?: boolean;
}

const GLOBAL_FEEDBACK_PATH = '/global-feedback/';

// Mirrors Django's `|urlencode` filter (urllib quote with safe="/").
function djangoUrlencode(value: string): string {
  return encodeURIComponent(value)
    .replace(/%2F/gi, '/')
    .replace(/[!'()*]/g, (char) => `%${char.charCodeAt(0).toString(16).toUpperCase()}`);
}

// Mirrors banner.html: `{{ support }}?url={{ current_host }}{{ current_path }}` where
// current_host is request.get_host() (host[:port], no scheme) and current_path is
// request.get_full_path()|urlencode.
function globalFeedbackHref(): string {
  const { host, pathname, search } = window.location;
  return `${wwwPath(GLOBAL_FEEDBACK_PATH)}?url=${host}${djangoUrlencode(`${pathname}${search}`)}`;
}

const subscribeToNothing = () => () => undefined;

export function PhaseBanner({ hideGlobalFeedback = false }: PhaseBannerProps) {
  // Re-renders on client navigation, which re-reads window.location below. The
  // server snapshot is the bare link so hydration matches.
  const pathname = usePathname();
  const href = useSyncExternalStore(
    subscribeToNothing,
    globalFeedbackHref,
    () => wwwPath(GLOBAL_FEEDBACK_PATH),
  );
  const shouldHideGlobalFeedback =
    hideGlobalFeedback || pathname.replace(/\/$/, '') === GLOBAL_FEEDBACK_PATH.replace(/\/$/, '');

  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">BETA</strong>
        <span className="govuk-phase-banner__text">
          This is a new service – your{' '}
          {shouldHideGlobalFeedback ? (
            'feedback'
          ) : (
            <a
              href={href}
              className="govuk-link"
              onClick={(event) => {
                // Query string may have changed without a pathname change.
                event.currentTarget.href = globalFeedbackHref();
              }}
            >
              feedback
            </a>
          )}{' '}
          will help us to improve it.
        </span>
      </p>
    </div>
  );
}
