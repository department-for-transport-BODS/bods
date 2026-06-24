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
              You can view data feeds on your data feeds page. The data will now be live for everyone else to see.
            </p>

            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />
            <div className="govuk-button-group">
              <Link role="button" className="govuk-button" href={`/publish/org/${orgId}/dataset/avl`}>
                View data feeds
              </Link>
              <Link className="govuk-link" href={`/publish/org/${orgId}/dataset/avl/${datasetId}/review`}>
                Back to review
              </Link>
            </div>
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
        </div>
      </div>
    </div>
  );
}
