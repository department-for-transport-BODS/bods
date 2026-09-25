import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { dataPath, publishAppPath, publishPath, wwwPath } from '@/config/client';

export default function GuidancePage() {
  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Bus Open Data Service', href: wwwPath('/') },
          { label: 'Publish Bus Open Data', href: publishPath('/') },
          { label: 'Guidance', href: publishAppPath('/guidance'), current: true },
        ]}
      />
      <main className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">Guidance</h1>
            <p className="govuk-body-l">
              What you need to know to get started. Find guidance and support material tailored to
              your needs.
            </p>
            <ul className="govuk-list govuk-list--spaced">
              <li>
                <Link className="govuk-link" href={publishAppPath('/guidance/operator-requirements')}>
                  Bus operator requirements
                </Link>
              </li>
              <li>
                <Link className="govuk-link" href={publishAppPath('/guidance/local-authority-requirements')}>
                  Local authority requirements
                </Link>
              </li>
              <li>
                <Link className="govuk-link" href={publishAppPath('/guidance/data-quality-definitions')}>
                  Data quality observations
                </Link>
              </li>
              <li>
                <Link className="govuk-link" href={publishAppPath('/guidance/score-description')}>
                  Data quality score description
                </Link>
              </li>
            </ul>
          </div>
          <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Interested in how data is used?</h2>
            <ul className="govuk-list govuk-list--spaced">
              <li>
                <a
                  className="govuk-link"
                  href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  About open bus data service
                </a>
              </li>
              <li>
                <Link className="govuk-link" href={dataPath('/guidance/requirements')}>
                  Developer documentation
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
