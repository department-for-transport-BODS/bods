/**
 * Bus Operator Requirements Page
 * 
 * Source: transit_odp/guidance/templates/guidance/bus_operators/base.html
 * View: transit_odp/guidance/views.py - BusOperatorReqView
 * 
 * This is a sectioned guidance page with navigation between sections.
 * Sections are defined in the sections/ directory, each corresponding
 * to a Django template file.
 */

'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { HOSTS } from '@/config';
import { PaginationPrevIcon, PaginationNextIcon } from '@/components/shared/PaginationIcons';

import {
  OverviewSection,
  WhoPublishesSection,
  RegisteringSection,
  AgentsSection,
  PublishingSection,
  DescriptionsSection,
  TimetablesSection,
  BusLocationSection,
  FaresSection,
  DataQualitySection,
  HelpSection,
} from './sections';

interface Section {
  name: string;
  title: string;
}

const SECTIONS: Section[] = [
  { name: 'overview', title: 'Overview' },
  { name: 'whopublishes', title: 'Who must publish open data?' },
  { name: 'registering', title: 'Using our account' },
  { name: 'agents', title: 'Agents' },
  { name: 'publishing', title: 'Publishing data' },
  { name: 'descriptions', title: 'Writing data descriptions' },
  { name: 'timetables', title: 'Timetables data' },
  { name: 'buslocation', title: 'Bus location data' },
  { name: 'fares', title: 'Fares data' },
  { name: 'dataquality', title: 'Data quality' },
  { name: 'help', title: 'How to get help' },
];

function SectionContent({ section }: { section: string }) {
  switch (section) {
    case 'overview':
      return <OverviewSection />;
    case 'whopublishes':
      return <WhoPublishesSection />;
    case 'registering':
      return <RegisteringSection />;
    case 'agents':
      return <AgentsSection />;
    case 'publishing':
      return <PublishingSection />;
    case 'descriptions':
      return <DescriptionsSection />;
    case 'timetables':
      return <TimetablesSection />;
    case 'buslocation':
      return <BusLocationSection />;
    case 'fares':
      return <FaresSection />;
    case 'dataquality':
      return <DataQualitySection />;
    case 'help':
      return <HelpSection />;
    default:
      return <OverviewSection />;
  }
}

/**
 * Pagination Navigation
 * Source: transit_odp/guidance/templates/guidance/snippets/previous_section.html
 * Source: transit_odp/guidance/templates/guidance/snippets/next_section.html
 */
function PaginationNav({ currentSection }: { currentSection: string }) {
  const currentIndex = SECTIONS.findIndex(s => s.name === currentSection);
  const prevSection = currentIndex > 0 ? SECTIONS[currentIndex - 1] : null;
  const nextSection = currentIndex < SECTIONS.length - 1 ? SECTIONS[currentIndex + 1] : null;

  return (
    <div className="govuk-!-margin-top-6">
      {prevSection && (
        <nav className="govuk-pagination govuk-pagination--block govuk-!-margin-bottom-1" role="navigation" aria-label="Pagination Prev">
          <div className="govuk-pagination__prev">
            <Link className="govuk-link govuk-pagination__link" href={`?section=${prevSection.name}`} rel="prev">
              {PaginationPrevIcon}
              <span className="govuk-pagination__link-title">Previous<span className="govuk-visually-hidden"> page</span></span>
              <span className="govuk-visually-hidden">:</span>
              <span className="govuk-pagination__link-label">{prevSection.title}</span>
            </Link>
          </div>
        </nav>
      )}
      {nextSection && (
        <nav className="govuk-pagination govuk-pagination--block govuk-!-margin-bottom-1" role="navigation" aria-label="Pagination Next">
          <div className="govuk-pagination__next">
            <Link className="govuk-link govuk-pagination__link" href={`?section=${nextSection.name}`} rel="next">
              {PaginationNextIcon}
              <span className="govuk-pagination__link-title">Next<span className="govuk-visually-hidden"> page</span></span>
              <span className="govuk-visually-hidden">:</span>
              <span className="govuk-pagination__link-label">{nextSection.title}</span>
            </Link>
          </div>
        </nav>
      )}
    </div>
  );
}

function BusOperatorRequirementsContent() {
  const searchParams = useSearchParams();
  const section = searchParams.get('section') || 'overview';

  return (
    <div className="govuk-width-container">
      <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href={HOSTS.root}>
              Bus Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/">
              Publish Bus Open Data
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            Bus operator requirements
          </li>
        </ol>
      </nav>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Bus operator requirements</h1>
            <p className="govuk-body-l">
              What you need to know to get started. Find guidance and support
              material tailored to your needs.
            </p>
            <ul className="govuk-list">
              {SECTIONS.map((s) => (
                <li key={s.name} className="govuk-!-padding-bottom-1">
                  <Link
                    className={`govuk-link ${s.name === section ? 'govuk-!-font-weight-bold' : ''}`}
                    href={`?section=${s.name}`}
                  >
                    {s.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <SectionContent section={section} />
            <PaginationNav currentSection={section} />
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-s">Related content</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <Link className="govuk-link" href="/guidance/support/local-authorities">
                  Local authority requirements
                </Link>
              </li>
              <li>
                <Link className="govuk-link" href="/contact">
                  Contact the Bus Open Data Service
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BusOperatorRequirementsPage() {
  return (
    <Suspense fallback={<div className="govuk-width-container"><p className="govuk-body">Loading...</p></div>}>
      <BusOperatorRequirementsContent />
    </Suspense>
  );
}
