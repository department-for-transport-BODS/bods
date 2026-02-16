import Link from 'next/link';

export default function Home() {
  return (
    <>
      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <h1 className="govuk-heading-xl app-masthead__title">
                Find bus open data
              </h1>
              <p className="govuk-body app-masthead__description">
                The Bus Open Data Service provides bus timetable, vehicle location and fares data
                for every local bus service in England.
              </p>
              <Link
                href="/guidance/support/developer"
                className="govuk-button app-button--inverted govuk-!-margin-bottom-0 govuk-button--start"
                role="button"
              >
                Guide Me
                <svg
                  className="govuk-button__start-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  width="17.5"
                  height="19"
                  viewBox="0 0 33 40"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <p className="govuk-body">
                <Link href="/data" className="govuk-link-bold">
                  Browse data
                </Link>
              </p>
              <p className="govuk-body">
                View and download open data published by operators of local bus and coach services.
              </p>
              <hr className="govuk-section-break govuk-section-break--xl" />

              <p className="govuk-body">
                <a className="govuk-link-bold" href="/api/timetable-openapi/" target="_blank" rel="noopener noreferrer">
                  API services
                </a>
              </p>
              <p className="govuk-body">
                Experiment with our interactive API services to familiarise yourself with data sets.
              </p>
              <hr className="govuk-section-break govuk-section-break--xl" />

              <p className="govuk-body">
                <Link href="/account/login" className="govuk-link-bold">
                  Download data
                </Link>
              </p>
              <p className="govuk-body">
                Download updates or all of the data published on BODS with a registered account.
              </p>
              <hr className="govuk-section-break govuk-section-break--xl" />

              <p className="govuk-body">
                <Link href="/data" className="govuk-link-bold">
                  View operator profiles
                </Link>
              </p>
              <p className="govuk-body">
                Search all operator profiles available on BODS to view associated data, NOC codes and licence numbers.
              </p>
              <hr className="govuk-section-break govuk-section-break--xl" />

              <p className="govuk-body">
                <a className="govuk-link-bold" href="/api/v1/dataset/" target="_blank" rel="noopener noreferrer">
                  Download the data catalogue
                </a>
              </p>
              <p className="govuk-body">
                Data catalogue will provide you with a comprehensive view of all data published on BODS and provide matching information between different dataset types.
              </p>
              <hr className="govuk-section-break govuk-section-break--xl" />

              <p className="govuk-body">
                <Link href="/data" className="govuk-link-bold">
                  View local transport authority details
                </Link>
              </p>
              <p className="govuk-body">
                Search all Local Transport Authority profiles to review the quality of published data.
              </p>
            </div>

            <div className="govuk-grid-column-one-third">
              <h2 className="govuk-heading-m">Need further help?</h2>
              <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                <li>
                  <a className="govuk-link" href="/api/v1/dataset/" target="_blank" rel="noopener noreferrer">
                    Data catalogue field definitions
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
