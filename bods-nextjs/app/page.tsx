/**
 * Home Page (www subdomain)
 * 
 * Source: transit_odp/templates/pages/home.html
 * This is the main landing page for the Bus Open Data Service.
 */

import Link from 'next/link';

export default function Home() {
  return (
    <>
      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <h1 className="govuk-heading-xl app-masthead__title">
                Bus Open Data Service
              </h1>
              <p className="govuk-body">
                The Bus Open Data Service provides bus timetable, vehicle location and
                fares data for every local bus service in England.
              </p>
              <p className="govuk-body">
                Follow us on Twitter{' '}
                <a
                  className="app-a--inverted"
                  href="https://twitter.com/busopendata"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  @busopendata
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <div>
                <h2 className="govuk-heading-m">Publish bus open data</h2>
                <p className="govuk-body">
                  This service is for operators of local bus services in England.
                </p>
                <ul className="govuk-list">
                  <li className="govuk-!-margin-bottom-4">
                    <Link href="/publish" className="govuk-link govuk-link-bold">
                      Publish bus data
                    </Link>
                  </li>
                  <li className="govuk-!-margin-bottom-4">
                    <Link href="/guidance/support/bus-operators" className="govuk-link govuk-link-bold">
                      View bus operator requirements
                    </Link>
                  </li>
                  <li className="govuk-!-margin-bottom-4">
                    <Link href="/guidance/support/local-authorities" className="govuk-link govuk-link-bold">
                      View local authority requirements
                    </Link>
                  </li>
                  <li>
                    <Link href="/publish/guide-me" className="govuk-link govuk-link-bold">
                      Guide me
                    </Link>
                  </li>
                </ul>
              </div>

              <div className="govuk-!-margin-top-8">
                <h2 className="govuk-heading-m">Find bus open data</h2>
                <p className="govuk-body">
                  This service provides timetables, bus location, and fares data for local
                  bus services across England. It is free open data, and does not require a
                  licence. Simply start using the APIs or downloading data for your
                  analysis, apps, products or services.
                </p>
                <ul className="govuk-list">
                  <li className="govuk-!-margin-bottom-4">
                    <Link href="/data" className="govuk-link govuk-link-bold">
                      Find bus open data
                    </Link>
                  </li>
                  <li>
                    <Link href="/guidance/support/developer" className="govuk-link govuk-link-bold">
                      View developer documentation
                    </Link>
                  </li>
                </ul>
              </div>
            </div>

            <div className="govuk-grid-column-one-third govuk-!-padding-top-5">
              <h2 className="govuk-heading-m">Public information</h2>
              <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                <li>
                  <a
                    className="govuk-link"
                    href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    About the Bus Open Data Service
                  </a>
                </li>
                <li>
                  <Link href="/changelog" className="govuk-link">
                    Service changelog
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="govuk-link">
                    Contact us for technical issues
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
