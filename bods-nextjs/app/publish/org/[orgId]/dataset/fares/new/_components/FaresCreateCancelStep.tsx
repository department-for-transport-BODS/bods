'use client';

import { publishAppPath } from '@/config/client';
import styles from './FaresCreateCancelStep.module.css';

// Mirrors Django `fares/feed_publish_cancel.html`.
export function FaresCreateCancelStep({ orgId, onBack }: Readonly<{ orgId: string; onBack: () => void }>) {
  return (
    <>
      <div className="govuk-breadcrumbs">
        <button type="button" className={`govuk-back-link govuk-button-back-link ${styles.backButton}`} onClick={onBack}>
          Back
        </button>
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Would you like to cancel publishing this data set?</h1>
            <p className="govuk-body">Any changes you have made so far will not be saved.</p>
            <div className="btn-group-justified">
              <a role="button" className="govuk-button app-!-mr-sm-4" href={publishAppPath(`/org/${orgId}/dataset/fares`)}>
                Confirm
              </a>
              <button type="button" className="govuk-button govuk-button--secondary" onClick={onBack}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
