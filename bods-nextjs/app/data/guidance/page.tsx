import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS, dataPath, publishAppPath } from '@/config/client';

export default function GuidancePage() {
  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Bus Open Data Service', href: HOSTS.www },
          { label: 'Find Bus Open Data Service', href: HOSTS.data },
          { label: 'Guidance', current: true },
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
            <p className="govuk-body-m">
              <Link className="govuk-link" href={dataPath('/guidance/requirements')}>
                Developer documentation
              </Link>
            </p>
            <p className="govuk-body-m">
              <a
                className="govuk-link"
                href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
                target="_blank"
                rel="noopener noreferrer"
              >
                About open bus data service
              </a>
            </p>
          </div>
          <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Interested in publisher requirements?</h2>
            <p className="govuk-body">
              <Link className="govuk-link" href={publishAppPath('/guidance/operator-requirements')}>
                Bus operator requirements
              </Link>
            </p>
            <p className="govuk-body">
              <Link className="govuk-link" href={publishAppPath('/guidance/local-authority-requirements')}>
                Local authority requirements
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
