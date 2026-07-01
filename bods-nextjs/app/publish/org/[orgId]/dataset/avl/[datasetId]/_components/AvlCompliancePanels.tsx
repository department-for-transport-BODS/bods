'use client';

import Link from 'next/link';
import { AvlFeedDetail } from './AvlFeedDetailContent';

interface AvlCompliancePanelsProps {
  feedDetail: AvlFeedDetail;
  orgId: string;
  datasetId: string;
}

export function AvlCompliancePanels({ feedDetail, orgId, datasetId }: AvlCompliancePanelsProps) {
  const status = feedDetail.avlComplianceStatus;
  const validationReportUrl = `/api/avl/download-validation-report/${feedDetail.datasetId}`;
  const matchingReportUrl = `/api/avl/download-matching-report/${feedDetail.datasetId}`;

  // No panel for compliant status
  if (status === 'Compliant') {
    return null;
  }

  if (status === 'Awaiting publisher review') {
    return (
      <div className="govuk-warning-text govuk-!-margin-bottom-7">
        <span className="govuk-warning-text__icon" aria-hidden="true">
          !
        </span>
        <strong className="govuk-warning-text__text">
          <span className="govuk-warning-text__assistive">Warning</span>
          <p className="govuk-body">
            Your data is currently being published but contains potential issues. Please correct these as per the
            email sent and update the data feed.
            {feedDetail.status === 'draft' && <span> If no corrections are made your feed will be unpublished.</span>}
          </p>
          <Link href={validationReportUrl} className="govuk-link">
            Download validation report
          </Link>
        </strong>
      </div>
    );
  }

  if (status === 'Partially compliant') {
    return (
      <div className="govuk-warning-text govuk-!-margin-bottom-7">
        <span className="govuk-warning-text__icon" aria-hidden="true">
          !
        </span>
        <strong className="govuk-warning-text__text">
          <span className="govuk-warning-text__assistive">Warning</span>
          <p className="govuk-body govuk-!-margin-bottom-1">The AVL data feed is only partially compliant.</p>
          <p className="govuk-body">To fully pass validation please address all outstanding issues in the validation report and update the data feed</p>
          <Link href={validationReportUrl} className="govuk-link">
            Download validation report
          </Link>
        </strong>
      </div>
    );
  }

  if (status === 'Non-compliant') {
    return (
      <div className="govuk-error-summary govuk-!-margin-bottom-7" role="alert">
        <h2 className="govuk-error-summary__title">Data feed not compliant</h2>
        <div className="govuk-error-summary__body">
          <p className="govuk-body">
            The AVL data feed is non-compliant. To address this, please update the data feed with a correctly
            formatted file.
          </p>
          <Link href={validationReportUrl} className="govuk-link">
            Download validation report
          </Link>
        </div>
      </div>
    );
  }

  return null;
}
