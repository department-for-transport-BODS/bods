import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleExclamation } from '@fortawesome/free-solid-svg-icons';

interface AvlTimetableMatchingProps {
  matching?: string;
  datasetId: number;
  orgId: string;
}

export function AvlTimetableMatching({ matching, datasetId, orgId }: AvlTimetableMatchingProps) {
  const matchingReportUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/download-matching-report`;

  return (
    <div>
      <p className="govuk-body govuk-!-margin-bottom-0">
        {!matching || matching === '0%' ? (
          <>
            <FontAwesomeIcon icon={faCircleExclamation} aria-hidden="true" />
            {' Pending '}
          </>
        ) : (
          <>
            {matching !== '100%' && <FontAwesomeIcon icon={faCircleExclamation} aria-hidden="true" />}
            {matching} completely matched AVL to Timetables
          </>
        )}
      </p>
      {matching && matching !== '0%' && (
        <Link href={matchingReportUrl} className="govuk-link govuk-!-margin-left-5 govuk-!-margin-top-1">
          Download matching report
        </Link>
      )}
    </div>
  );
}
