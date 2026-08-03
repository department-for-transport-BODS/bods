/**
 * Not Found Page for Dataset Detail
 * 
 * 
 * Displayed when a dataset ID doesn't exist
 */

import Link from 'next/link';

export default function DatasetNotFound() {
  return (
    <div className="govuk-width-container">
      <main className="govuk-main-wrapper" id="main-content" role="main">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Dataset not found</h1>
            <p className="govuk-body">
              The dataset you are looking for could not be found. It may have been removed or the ID may be incorrect.
            </p>
            <p className="govuk-body">
              You can:
            </p>
            <ul className="govuk-list govuk-list--bullet">
              <li>
                <Link href="/data" className="govuk-link">
                  Browse all datasets
                </Link>
              </li>
              <li>
                <Link href="/data?status=live" className="govuk-link">
                  View published datasets
                </Link>
              </li>
              <li>
                <Link href="/contact" className="govuk-link">
                  Contact us for support
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
