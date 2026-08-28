import Link from 'next/link';
import { dataPath, wwwPath } from '@/config/client';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

export const metadata = {
  title: 'Find bus open data - Bus Open Data Service',
  description:
    'The Bus Open Data Service provides bus timetable, vehicle location and fares data for every local bus service in England.',
};

export default function DataHomePage() {
  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
          <Breadcrumbs items={hostBreadcrumbs('data', { label: 'Find Bus Open Data', current: true })} />
        </div>
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <h1 className="govuk-heading-xl app-masthead__title">Find bus open data</h1>
              <p className="govuk-body">
                The Bus Open Data Service provides bus timetable, vehicle location and fares data for
                every local bus service in England.
              </p>
              <Link
                href={dataPath('/guide-me')}
                role="button"
                draggable={false}
                className="govuk-button app-button--inverted govuk-!-margin-bottom-0 govuk-button--start"
                data-module="govuk-button"
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
        <main className="govuk-main-wrapper" id="main-content" role="main">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <div className="govuk-!-padding-right-9">
                <p className="govuk-body">
                  <Link className="govuk-link-bold" href={dataPath('/search')}>
                    Browse data
                  </Link>
                </p>
                <p className="govuk-body">
                  View and download open data published by operators of local bus and coach services.
                </p>
                <hr className="govuk-section-break govuk-section-break--xl" />

                <p className="govuk-body">
                  <Link className="govuk-link-bold" href={dataPath('/api')}>
                    API services
                  </Link>
                </p>
                <p className="govuk-body">
                  Experiment with our interactive API services to familiarise yourself with data sets.
                </p>
                <hr className="govuk-section-break govuk-section-break--xl" />

                <p className="govuk-body">
                  <Link className="govuk-link-bold" href={dataPath('/downloads')}>
                    Download data
                  </Link>
                </p>
                <p className="govuk-body">
                  Download updates or all of the data published on BODS with a registered account.
                </p>
                <hr className="govuk-section-break govuk-section-break--xl" />

                <p className="govuk-body">
                  <Link className="govuk-link-bold" href={dataPath('/operators')}>
                    View operator profiles
                  </Link>
                </p>
                <p className="govuk-body">
                  Search all operator profiles available on BODS to view associated data, NOC codes and
                  licence numbers.
                </p>
                <hr className="govuk-section-break govuk-section-break--xl" />

                <p className="govuk-body">
                  <Link className="govuk-link-bold" href={dataPath('/catalogue')}>
                    Download the data catalogue
                  </Link>
                </p>
                <p className="govuk-body">
                  Data catalogue will provide you with a comprehensive view of all data published on BODS
                  and provide matching information between different dataset types.
                </p>
                <hr className="govuk-section-break govuk-section-break--xl" />

                <p className="govuk-body">
                  <Link className="govuk-link-bold" href={dataPath('/local-authority')}>
                    View local transport authority details
                  </Link>
                </p>
                <p className="govuk-body">
                  Search all Local Transport Authority profiles to review the quality of published data.
                </p>
              </div>
            </div>

            <div className="govuk-grid-column-one-third">
              <h2 className="govuk-heading-m">Need further help?</h2>
              <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                <li>
                  <Link
                    className="govuk-link"
                    href={dataPath('/guidance/requirements?section=datacatalogue')}
                  >
                    Data catalogue field definitions
                  </Link>
                </li>
                <li>
                  <Link className="govuk-link" href={wwwPath('/changelog')}>
                    Service changelog
                  </Link>
                </li>
                <li>
                  <Link className="govuk-link" href={wwwPath('/contact')}>
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
