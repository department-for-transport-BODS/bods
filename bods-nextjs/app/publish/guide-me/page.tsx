import Link from 'next/link';
interface StepItem {
  title: string;
  links: Array<{ label: string; href: string; copy: string }>;
}

const STEPS: StepItem[] = [
  {
    title: 'Read supporting documents',
    links: [
      {
        label: 'View user guide',
        href: '/guidance/support/bus-operators?section=publishing',
        copy: 'The user guide includes an overview, the schema, guidance, requirements, and the best practices for publishing BODS data.',
      },
    ],
  },
  {
    title: 'Set up your account',
    links: [
      {
        label: 'Invite members and agents',
        href: '/account/manage/invite/',
        copy: 'Invite other members from your organisations and / or agents who will act on your behalf to publish data.',
      },
      {
        label: 'Update profile',
        href: '/publish/guide-me/profile/',
        copy: 'Update your profile including licence number and NOC codes. Please make sure your profile information is correct and up to date.',
      },
    ],
  },
  {
    title: 'Publish open data',
    links: [
      {
        label: 'Publish data',
        href: '/publish/guide-me/publish/',
        copy: 'Make your data open by publishing Timetable, Location and Fare data.',
      },
      {
        label: 'Understanding validation checks',
        href: '/guidance/support/bus-operators?section=dataquality',
        copy: 'Read the guidance on post publishing validation and data quality reports to understand how to interpret and action them.',
      },
    ],
  },
  {
    title: 'Review your data',
    links: [
      {
        label: 'View publisher dashboard',
        href: '/publish/guide-me/dashboard/',
        copy: 'Review all datasets published on BODS from your organisation account and keep track of your data health.',
      },
      {
        label: 'View data consumers activity',
        href: '/publish/guide-me/activity/',
        copy: 'View stats on how data consumers are utilising and interacting with your published data.',
      },
    ],
  },
];

export default function PublishGuideMePage() {

  return (
    <div className="govuk-width-container">
      <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/data">
              Bus Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/publish">
              Publish Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            Guide me
          </li>
        </ol>
      </nav>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Guide me</h1>
            <p className="govuk-body">
              We advise all users to review the following guidance for a better Bus Open Data
              Service (BODS) experience.
            </p>
            <p className="govuk-body">
              For all the key dates and requirements for publishing data on BODS{' '}
              <a
                className="govuk-link govuk-!-font-size-19"
                href="https://www.gov.uk/government/collections/bus-open-data-service"
                target="_blank"
                rel="noopener noreferrer"
              >
                access the data requirement guidance.
              </a>
            </p>

            <ol className="app-step-nav__steps">
              {STEPS.map((step, index) => (
                <li key={step.title} className="app-step-nav__step js-step">
                  <div className="app-step-nav__header js-toggle-panel" data-position={index + 1}>
                    <h2 className="app-step-nav__title">
                      <span className="app-step-nav__circle app-step-nav__circle--number">
                        <span className="app-step-nav__circle-inner">
                          <span className="app-step-nav__circle-background">
                            <span className="govuk-visually-hidden">Step</span> {index + 1}
                          </span>
                        </span>
                      </span>
                      <span className="js-step-title">
                        <span className="js-step-title-text">{step.title}</span>
                      </span>
                    </h2>
                  </div>
                  <div className="app-step-nav__panel">
                    {step.links.map((item) => (
                      <div key={item.label}>
                        <a className="govuk-link govuk-!-font-size-19" href={item.href}>
                          {item.label}
                        </a>
                        <p className="govuk-body app-step-nav__paragraph">{item.copy}</p>
                      </div>
                    ))}
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need further help?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a
                  className="govuk-link"
                  href="https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  National Operator Code
                </a>
              </li>
              <li>
                <Link className="govuk-link" href="/changelog">
                  Service changelog
                </Link>
              </li>
              <li>
                <a
                  className="govuk-link"
                  href="https://www.gov.uk/government/publications/bus-open-data-implementation-guide/bus-open-data-implementation-guide#glossary-of-terms"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Glossary of terms
                </a>
              </li>
              <li>
                <Link className="govuk-link" href="/contact">
                  Contact us for technical issues
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

