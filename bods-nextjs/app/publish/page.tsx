'use client';

/**
 * Publish home page
 *
 * Entry page for publishing bus open data.
 */

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS, publishAppPath, wwwPath } from '@/config/client';
import { useAuth } from '@/hooks/useAuth';
import { getPublishHomeLinks, isAbodsUser } from '@/lib/publish-home-links';

function PublishDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const abodsUser = isAbodsUser(user);

  // Django's PublishHomeView.dispatch sends signed-in abods users straight to the abods gatekeeper.
  useEffect(() => {
    if (abodsUser) {
      router.replace(publishAppPath('/abods-gatekeeper'));
    }
  }, [abodsUser, router]);

  if (abodsUser) {
    return null;
  }

  const { startView, reviewView } = getPublishHomeLinks(user);

  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
          <Breadcrumbs
            items={[
              { label: 'Bus Open Data Service', href: HOSTS.www },
              { label: 'Publish Bus Open Data', current: true },
            ]}
          />
        </div>
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-left-0 govuk-!-padding-right-9 publish-home-masthead-copy">
              <h1 className="govuk-heading-xl app-masthead__title">Publish bus open data</h1>
              <p className="govuk-body">Use this service to publish the following data:</p>
              <ul className="govuk-body">
                <li>Bus routes and timetable</li>
                <li>Automatic Vehicle Location (AVL)</li>
                <li>Fares</li>
              </ul>
              <Link
                href={startView}
                className="govuk-button app-button--inverted govuk-!-margin-bottom-0 govuk-button--start"
              >
                Publish data
                <svg
                  className="govuk-button__start-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  width="17.5"
                  height="19"
                  viewBox="0 0 33 40"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row govuk-!-margin-bottom-8">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <h2 className="govuk-heading-s">
                <Link className="govuk-link-bold" href={publishAppPath('/guide-me')}>
                  Guide me
                </Link>
              </h2>
              <p className="govuk-body govuk-!-margin-bottom-7">
                Get started publishing data to BODS and learn about the different feature and requirements.
              </p>

              <h2 className="govuk-heading-s">
                <Link className="govuk-link-bold" href={reviewView}>
                  Review my data
                </Link>
              </h2>
              <p className="govuk-body govuk-!-margin-bottom-7">Review the health of your data.</p>

              <h2 className="govuk-heading-s">
                <Link className="govuk-link-bold" href="/account">
                  Manage your account
                </Link>
              </h2>
              <p className="govuk-body govuk-!-margin-bottom-7">
                View or edit NOC codes, licence numbers and other information related to your account.
              </p>
            </div>

            <div className="govuk-grid-column-one-third">
              <h2 className="govuk-heading-m">Need further help?</h2>
              <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                <li>
                  <Link className="govuk-link" href={wwwPath('/changelog')}>
                    Service changelog
                  </Link>
                </li>
                <li>
                  <Link className="govuk-link" href={wwwPath('/contact')}>
                    Contact us for technical issues
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function PublishPage() {
  return (
    <ProtectedRoute>
      <PublishDashboard />
    </ProtectedRoute>
  );
}
