'use client';

/**
 * Signed-out confirmation.
 *
 * Mirrors Django's account/logout_success.html (LogoutSuccessView), including
 * clearing caches and web storage.
 */

import { useEffect } from 'react';
import { HOSTS } from '@/config/client';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

export default function LogoutSuccessPage() {
  const area = useBodsArea();

  useEffect(() => {
    if ('caches' in window) {
      caches.keys().then((names) => {
        names.forEach((name) => {
          caches.delete(name);
        });
      });
    }

    try {
      window.localStorage.clear();
      window.sessionStorage.clear();
    } catch {
      // Storage can be unavailable.
    }
  }, []);

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          area,
          { label: 'My account', href: '/account' },
          { label: 'Sign out', current: true },
        )}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Signed out</h1>
            <p className="govuk-body-l">You have successfully signed out from your account</p>
            <p className="govuk-body-l">
              <a className="govuk-link" href={HOSTS[area]}>
                Return to the homepage
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
