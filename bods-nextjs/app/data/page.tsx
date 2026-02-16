import Link from 'next/link';
import { HOSTS } from '@/lib/config';

export default function DataBrowsePage() {
  return (
    <>
      <div className="govuk-width-container">
        <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <a className="govuk-breadcrumbs__link" href={HOSTS.root}>
                Bus Open Data Service
              </a>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/">
                Find Bus Open Data
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">
              Browse
            </li>
          </ol>
        </nav>
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-left-0 govuk-!-padding-right-9">
              <h1 className="govuk-heading-xl app-masthead__title">Browse bus open data</h1>
              <p className="govuk-body">
                You can browse the individual data sets or data feeds provided by the publishers.
                By clicking on a data set or data feed you can see its metadata, description and
                more information. You can also subscribe, download or use the API for specific data
                from the browse section with a registered account.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <main className="govuk-main-wrapper" id="main-content" role="main">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <div className="govuk-!-padding-right-9">
                <div className="govuk-grid-row">
                  <a className="govuk-link-bold govuk-body" href="/data/timetables?status=live">
                    Timetables data
                  </a>
                  <p className="govuk-body govuk-!-padding-top-3">
                    You can filter and browse specific timetables data on the service.
                  </p>
                  <ul className="govuk-list">
                    <li><strong>Format:</strong> TXC 2.4 PTI 1.1.A</li>
                    <li><strong>File type:</strong> XML file</li>
                    <li><strong>Data type:</strong> Static</li>
                    <li><strong>Data source:</strong> BODS</li>
                  </ul>
                </div>

                <div className="govuk-grid-row govuk-!-margin-top-7">
                  <a className="govuk-link-bold govuk-body" href="/data/avl?status=live">
                    Location data
                  </a>
                  <p className="govuk-body govuk-!-padding-top-3">
                    You can filter and browse the live locations of buses at a specific point in
                    time.
                  </p>
                  <ul className="govuk-list">
                    <li><strong>Format:</strong> SIRI-VM</li>
                    <li><strong>File type:</strong> XML file</li>
                    <li><strong>Data type:</strong> Real-time</li>
                    <li><strong>Data source:</strong> BODS</li>
                  </ul>
                </div>

                <div className="govuk-grid-row govuk-!-margin-top-7">
                  <a className="govuk-link-bold govuk-body" href="/data/fares?status=live">
                    Fares data
                  </a>
                  <p className="govuk-body govuk-!-padding-top-3">
                    You can filter and browse specific fares data on the service.
                  </p>
                  <ul className="govuk-list">
                    <li><strong>Format:</strong> NeTEx</li>
                    <li><strong>File type:</strong> XML file</li>
                    <li><strong>Data type:</strong> Static</li>
                    <li><strong>Data source:</strong> BODS</li>
                  </ul>
                </div>

                <div className="govuk-grid-row govuk-!-margin-top-7">
                  <a className="govuk-link-bold govuk-body" href="/data/disruptions">
                    Disruption data
                  </a>
                  <p className="govuk-body govuk-!-padding-top-3">
                    You can browse specific disruption data.
                  </p>
                  <ul className="govuk-list">
                    <li><strong>Format:</strong> SIRI-SX</li>
                    <li><strong>File type:</strong> XML file</li>
                    <li><strong>Data type:</strong> Real-time</li>
                    <li><strong>Data source:</strong> Local authorities</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="govuk-grid-column-one-third">
              <h2 className="govuk-heading-m">Need further help?</h2>
              <ul className="govuk-list">
                <li className="govuk-!-margin-bottom-3">
                  <Link className="govuk-link" href="/guidance/support/developer">
                    Guide me
                  </Link>
                </li>
                <li className="govuk-!-margin-bottom-3">
                  <Link className="govuk-link" href="/changelog">
                    Service changelog
                  </Link>
                </li>
                <li className="govuk-!-margin-bottom-3">
                  <Link className="govuk-link" href="/contact">
                    Contact us for technical issues
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

/**
 * Metadata for the page
 */
export const metadata = {
  title: 'Browse - Bus Open Data Service',
  description: 'Browse bus open data by type, including timetables, location, fares and disruption data.',
};
