/**
 * Data Quality Reports Overview
 * 
 * Main page for data quality reports
 */

import Link from 'next/link';
import { dataPath } from '@/config/client';

export default function DataQualityPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Data quality reports</h1>
            <p className="govuk-body-l">
              View and download data quality reports for timetable datasets.
            </p>
            <ul className="govuk-list">
              <li>
                <Link href={dataPath('/dq/overview')} className="govuk-link">
                  Report overview
                </Link>
              </li>
              <li>
                <Link href={dataPath('/dq/csv')} className="govuk-link">
                  Download CSV report
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

