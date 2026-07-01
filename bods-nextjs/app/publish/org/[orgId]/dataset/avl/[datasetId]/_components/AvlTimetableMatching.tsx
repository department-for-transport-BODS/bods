'use client';

import Link from 'next/link';

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
            <i className="fas fa-exclamation-circle fa"></i>
            {' Pending '}
          </>
        ) : (
          <>
            {matching !== '100%' && <i className="fas fa-exclamation-circle fa"></i>}
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
