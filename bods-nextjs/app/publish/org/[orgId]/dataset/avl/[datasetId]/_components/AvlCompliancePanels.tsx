import Link from 'next/link';
import type { AvlFeedDetail } from './AvlFeedDetailContent';

enum AvlComplianceStatus {
  Compliant = 'Compliant',
  AwaitingPublisherReview = 'Awaiting publisher review',
  PartiallyCompliant = 'Partially compliant',
  NonCompliant = 'Non-compliant',
}

interface AvlCompliancePanelsProps {
  feedDetail: AvlFeedDetail;
}

export function AvlCompliancePanels({ feedDetail }: AvlCompliancePanelsProps) {
  const status = feedDetail.avlComplianceStatus;
  const validationReportUrl = `/publish/org/${feedDetail.organisationId}/dataset/avl/${feedDetail.datasetId}/validation-report/`;

  // No panel for compliant status
  if (status === AvlComplianceStatus.Compliant) {
    return null;
  }

  if (status === AvlComplianceStatus.AwaitingPublisherReview) {
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

  if (status === AvlComplianceStatus.PartiallyCompliant) {
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

  if (status === AvlComplianceStatus.NonCompliant) {
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
