'use client';

import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { PaginationPrevIcon, PaginationNextIcon } from '@/components/shared/PaginationIcons';
import {
  AgentSection,
  HelpSection,
  LocalAuthorityBusesSection,
  NaptanSection,
  OverviewSection,
  SupportSection,
  UsingBodsSection,
} from './sections';

interface Section {
  name: string;
  title: string;
}

const SECTIONS: Section[] = [
  { name: 'overview', title: 'Overview' },
  { name: 'support', title: 'Supporting operators' },
  { name: 'agent', title: 'Being an Agent' },
  { name: 'naptan', title: 'NaPTAN stop data' },
  {
    name: 'local-auth-buses',
    title: 'Providing data for Local Authority operated buses',
  },
  { name: 'usingbods', title: 'Using Bus Open Data' },
  { name: 'help', title: 'How to get help' },
];

function SectionContent({ section }: { section: string }) {
  switch (section) {
    case 'support':
      return <SupportSection />;
    case 'agent':
      return <AgentSection />;
    case 'naptan':
      return <NaptanSection />;
    case 'local-auth-buses':
      return <LocalAuthorityBusesSection />;
    case 'usingbods':
      return <UsingBodsSection />;
    case 'help':
      return <HelpSection />;
    default:
      return <OverviewSection />;
  }
}

function PaginationNav({ currentSection }: { currentSection: string }) {
  const currentIndex = SECTIONS.findIndex((s) => s.name === currentSection);
  const prevSection = currentIndex > 0 ? SECTIONS[currentIndex - 1] : null;
  const nextSection =
    currentIndex >= 0 && currentIndex < SECTIONS.length - 1
      ? SECTIONS[currentIndex + 1]
      : null;

  return (
    <div className="govuk-!-margin-top-6">
      {prevSection && (
        <nav
          className="govuk-pagination govuk-pagination--block govuk-!-margin-bottom-1"
          role="navigation"
          aria-label="Pagination Prev"
        >
          <div className="govuk-pagination__prev">
            <Link
              className="govuk-link govuk-pagination__link"
              href={`?section=${prevSection.name}`}
              rel="prev"
            >
              {PaginationPrevIcon}
              <span className="govuk-pagination__link-title">
                Previous
                <span className="govuk-visually-hidden"> page</span>
              </span>
              <span className="govuk-visually-hidden">:</span>
              <span className="govuk-pagination__link-label">{prevSection.title}</span>
            </Link>
          </div>
        </nav>
      )}
      {nextSection && (
        <nav
          className="govuk-pagination govuk-pagination--block govuk-!-margin-bottom-1"
          role="navigation"
          aria-label="Pagination Next"
        >
          <div className="govuk-pagination__next">
            <Link
              className="govuk-link govuk-pagination__link"
              href={`?section=${nextSection.name}`}
              rel="next"
            >
              {PaginationNextIcon}
              <span className="govuk-pagination__link-title">
                Next
                <span className="govuk-visually-hidden"> page</span>
              </span>
              <span className="govuk-visually-hidden">:</span>
              <span className="govuk-pagination__link-label">{nextSection.title}</span>
            </Link>
          </div>
        </nav>
      )}
    </div>
  );
}

function LocalAuthoritiesContent() {
  const searchParams = useSearchParams();
  const section = searchParams.get('section') || 'overview';

  return (
    <div className="govuk-width-container">
      <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/">
              Bus Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/publish">
              Publish Bus Open Data
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link
              className="govuk-breadcrumbs__link"
              href="/guidance/support/bus-operators"
            >
              Guidance
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            Local authority requirements
          </li>
        </ol>
      </nav>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Local authority requirements</h1>
            <p className="govuk-body-l">
              What you need to know to get started. Find guidance and support
              material tailored to your needs.
            </p>
            <ul className="govuk-body dashed">
              {SECTIONS.map((s) => (
                <li key={s.name} className="govuk-!-padding-bottom-1">
                  <Link
                    className={`govuk-link ${
                      s.name === section ? 'govuk-!-font-weight-bold' : ''
                    }`}
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
                <Link className="govuk-link" href="/guidance/support/bus-operators">
                  Bus operator requirements
                </Link>
              </li>
              <li>
                <Link className="govuk-link" href="/contact">
                  Support line
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LocalAuthoritiesRequirementsPage() {
  return (
    <Suspense
      fallback={
        <div className="govuk-width-container">
          <p className="govuk-body">Loading...</p>
        </div>
      }
    >
      <LocalAuthoritiesContent />
    </Suspense>
  );
}

