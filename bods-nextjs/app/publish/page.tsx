"use client";

/**
 * Publisher Dashboard Home
 * 
 * Main page for publishers (publish subdomain)
 */

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

function PublishDashboard() {
  const { user } = useAuth();

  // all publish navigation inside Next routes.
  let startView = '/publish/org';
  if (user?.organisation_id) {
    startView = `/publish/org/${user.organisation_id}/dataset`;
  }

  let reviewView = '/publish/org';
  if (user?.organisation_id) {
    reviewView = `/publish/org/${user.organisation_id}/dataset/fares`;
  }

  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
          <div className="govuk-breadcrumbs">
            <ol className="govuk-breadcrumbs__list">
              <li className="govuk-breadcrumbs__list-item">
                <Link className="govuk-breadcrumbs__link" href="/data">
                  Bus Open Data Service
                </Link>
              </li>
              <li className="govuk-breadcrumbs__list-item" aria-current="page">
                Publish Open Data Service
              </li>
            </ol>
          </div>
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
                <Link className="govuk-link-bold" href="/publish/guide-me">
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
                <Link className="govuk-link-bold" href="/publish/account">
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
                  <Link className="govuk-link" href="/changelog">
                    Service changelog
                  </Link>
                </li>
                <li>
                  <Link className="govuk-link" href="/contact">
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

