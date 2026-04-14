'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function FaresPublishSuccessContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const datasetDetailUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}`;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/data">
                Bus Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/publish">
                Publish Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset`}>
                Choose data type
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href={faresListUrl}>
                Fares Data Sets
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">
              Publish success
            </li>
          </ol>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <span className="govuk-caption-l">Fares data set successfully published</span>
            <h1 className="govuk-heading-xl">Changes to data set now live</h1>

            <p className="govuk-body-m">
              You have successfully published your fares data set and this information is now live.
            </p>

            <h2 className="govuk-heading-m">What happens next?</h2>
            <p className="govuk-body-m">
              You can view the data set on{' '}
              <Link className="govuk-link" href={faresListUrl}>
                your fares data sets
              </Link>{' '}
              or by clicking the button below. The data will now be live for everyone else to see.
            </p>

            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />

            <Link className="govuk-button" href={datasetDetailUrl}>
              View published data set
            </Link>

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
          <div className="govuk-grid-column-one-third"></div>
        </div>
      </div>
    </div>
  );
}

export default function FaresPublishSuccessPage() {
  return (
    <ProtectedRoute>
      <FaresPublishSuccessContent />
    </ProtectedRoute>
  );
}
