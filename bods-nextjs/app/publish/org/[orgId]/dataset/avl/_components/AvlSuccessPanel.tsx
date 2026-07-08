'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

type AvlSuccessPanelProps = {
  update: boolean;
};

export function AvlSuccessPanel({ update }: AvlSuccessPanelProps) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const listUrl = `/publish/org/${orgId}/dataset/avl`;
  const detailUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}`;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <div className="govuk-panel govuk-panel--confirmation">
              <h1 className="govuk-panel__title govuk-!-margin-8">
                Your data feed has been successfully {update ? 'updated' : 'published'}
              </h1>
            </div>
            <p className="govuk-body-m">We have sent you a confirmation email.</p>
          </div>
        </div>

        <div className="govuk-grid-row govuk-!-padding-top-3">
          <div className="govuk-grid-column-three-quarters">
            <h2 className="govuk-heading-m">What happens next?</h2>
            <p className="govuk-body-m">
              You can view the data feed on your{' '}
              <Link className="govuk-link" href={listUrl}>
                data feeds page
              </Link>{' '}
              or by clicking the button below. The data will now be live for everyone else to see.
            </p>
            <p className="govuk-body-m">
              Please note the introduction of a new SIRI-VM validator to ensure the highest quality data is provided to
              consumers.
            </p>
            <p className="govuk-body-m">
              The SIRI-VM validator will check the mandatory fields are populated 24 hours after publishing and if
              necessary an error report will be sent to you. If there are still missing fields at the end of 7 days
              the feed will change to a compliance error status. To learn more about the compliance error status and
              how it works please read the{' '}
              <Link className="govuk-link" href="/guidance/support/bus-operators?section=buslocation">
                guidance page.
              </Link>
            </p>

            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />
            <Link role="button" className="govuk-button" href={detailUrl}>
              View published data feed
            </Link>
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
        </div>
      </div>
    </div>
  );
}
