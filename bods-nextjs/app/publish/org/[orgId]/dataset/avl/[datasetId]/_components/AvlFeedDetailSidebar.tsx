'use client';

import Link from 'next/link';

export function AvlFeedDetailSidebar() {
  return (
    <div>
      <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          <Link className="govuk-link" href="/guidance/support/bus-operators/">
            View our guidelines here
          </Link>
        </li>
        <li>
          <Link className="govuk-link" href="/contact/">
            Contact support desk
          </Link>
        </li>
        <li>
          <Link className="govuk-link" href="/guidance/support/bus-operators/?section=dataquality">
            AVL feed compliance guidance
          </Link>
        </li>
        <li>
          <Link
            className="govuk-link"
            href="/guidance/support/bus-operators/?section=dataquality#avl-to-timetable-matching"
          >
            AVL to Timetables matching guidance
          </Link>
        </li>
      </ul>
    </div>
  );
}
