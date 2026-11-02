import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleExclamation } from '@fortawesome/free-solid-svg-icons';
import { publishAppPath } from '@/config/client';

interface AvlTimetableMatchingProps {
  matching?: string;
  datasetId: number;
  orgId: string;
}

export function AvlTimetableMatching({ matching, datasetId, orgId }: AvlTimetableMatchingProps) {
  const matchingReportUrl = publishAppPath(
    `/org/${orgId}/dataset/avl/${datasetId}/download-matching-report/`,
  );

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
        // Plain anchor: this is a file download served by a route handler, not a page.
        <a href={matchingReportUrl} className="govuk-link govuk-!-margin-left-5 govuk-!-margin-top-1">
          Download matching report
        </a>
      )}
    </div>
  );
}
