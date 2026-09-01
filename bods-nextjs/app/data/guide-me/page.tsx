import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { dataPath, wwwPath } from '@/config/client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

export const metadata = {
  title: 'Guide me - Bus Open Data Service',
  description:
    'Step by step guidance for finding, downloading and consuming data published on the Bus Open Data Service.',
};

interface StepLink {
  label: string;
  href: string;
  copy: string;
  external?: boolean;
}

interface Step {
  title: string;
  links: StepLink[];
}

const STEPS: Step[] = [
  {
    title: 'Read supporting documents',
    links: [
      {
        label: 'View user guide',
        href: dataPath('/guidance/requirements'),
        copy: 'The user guide includes the schema, road map and best practise using BODS data.',
      },
    ],
  },
  {
    title: 'See what is on BODS',
    links: [
      {
        label: 'Browse data',
        href: dataPath('/search'),
        copy: 'You can search and filter the database. You can also download the specific dataset or subscribe or copy the dataset Application Programming Interface (API).',
      },
      {
        label: 'Download the data catalogue',
        href: dataPath('/catalogue'),
        copy: 'Data catalogue will provide you with a comprehensive view of all data published on BODS and provide matching information between different dataset types.',
      },
    ],
  },
  {
    title: 'Get an account',
    links: [
      {
        label: 'Register your account',
        href: '/account/signup',
        copy: 'A BODS account is required to download data or use the API.',
      },
    ],
  },
  {
    title: 'Use download',
    links: [
      {
        label: 'Download data',
        href: dataPath('/downloads'),
        copy: 'You can filter or download all dataset published on BODS and additional data we provide.',
      },
    ],
  },
  {
    title: 'Use API',
    links: [
      {
        label: 'View developer documentation',
        href: dataPath('/guidance/requirements?section=api'),
        copy: 'We recommend checking the developer document to find out the parameters available.',
      },
      {
        label: 'API services',
        href: dataPath('/api'),
        copy: 'You can investigate the different API parameters present on BODS. This should inform you better on how to utilize the API for your particular use case.',
      },
      {
        label: 'Get my API key',
        href: '/account/settings',
        copy: 'Once you have registered you will be given an API key.',
      },
      {
        label: 'Case studies',
        href: dataPath('/guidance/requirements?section=casestudies'),
        copy: 'Helpful cases studies are provided to inspire and support your API data journey on BODS.',
      },
      {
        label: 'BODS Data Extractor Python Package',
        href: 'https://github.com/department-for-transport-BODS/bods-data-extractor',
        copy: 'A pre build set of Python functions to make it easier to find and extract BODS data from the API.',
        external: true,
      },
    ],
  },
];

function StepLinkItem({ item }: { item: StepLink }) {
  if (item.external) {
    return (
      <div>
        <a
          className="govuk-link govuk-!-font-size-19"
          href={item.href}
          target="_blank"
          rel="noopener noreferrer"
        >
          {item.label}
        </a>
        <p className="govuk-body app-step-nav__paragraph">{item.copy}</p>
      </div>
    );
  }

  return (
    <div>
      <Link className="govuk-link govuk-!-font-size-19" href={item.href}>
        {item.label}
      </Link>
      <p className="govuk-body app-step-nav__paragraph">{item.copy}</p>
    </div>
  );
}

export default function DataGuideMePage() {
  return (
    <div className="govuk-width-container">
      <Breadcrumbs items={hostBreadcrumbs('data', { label: 'Guide me', current: true })} />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Guide me</h1>
            <p className="govuk-body">
              We advise all users to review the following guidance for a better Bus Open Data
              Service (BODS) experience.
            </p>
            <p className="govuk-body">
              For a quick tour of what has been published on BODS{' '}
              <Link className="govuk-link govuk-!-font-size-19" href={dataPath('/catalogue')}>
                download the Data Catalogue
              </Link>
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
                      <StepLinkItem key={item.label} item={item} />
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
                <Link className="govuk-link" href={wwwPath('/changelog')}>
                  Service changelog
                </Link>
              </li>
              <li>
                <Link
                  className="govuk-link"
                  href={dataPath('/guidance/requirements?section=datacatalogue')}
                >
                  Data catalogue field definitions
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
      </div>
    </div>
  );
}
