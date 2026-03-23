'use client';

import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { config } from '@/config';
import { PaginationPrevIcon, PaginationNextIcon } from '@/components/shared/PaginationIcons';
import {
  ApiReferenceSection,
  BrowseDataSection,
  CaseStudiesSection,
  DataByOperatorSection,
  DataCatalogueSection,
  DataFormatsSection,
  DownloadingDataSection,
  HelpSection,
  MaintainingQualityDataSection,
  OverviewSection,
  QuickStartSection,
  UsingApiSection,
} from './sections';

interface Section {
  name: string;
  title: string;
}

const SECTIONS: Section[] = [
  { name: 'overview', title: 'Overview' },
  { name: 'quickstart', title: 'Quick start' },
  { name: 'datacatalogue', title: 'Data catalogue' },
  { name: 'databyoperator', title: 'Data by operator or location' },
  { name: 'browse', title: 'Browse for specific data' },
  { name: 'download', title: 'Downloading data' },
  { name: 'api', title: 'Using the APIs' },
  { name: 'apireference', title: 'API reference' },
  { name: 'dataformats', title: 'Data formats' },
  { name: 'maintainingqualitydata', title: 'Maintaining quality data' },
  { name: 'casestudies', title: 'Case studies' },
  { name: 'help', title: 'How to get help' },
];

function SectionContent({ section }: { section: string }) {
  switch (section) {
    case 'quickstart':
      return <QuickStartSection />;
    case 'datacatalogue':
      return <DataCatalogueSection />;
    case 'databyoperator':
      return <DataByOperatorSection />;
    case 'browse':
      return <BrowseDataSection />;
    case 'download':
      return <DownloadingDataSection />;
    case 'api':
      return <UsingApiSection />;
    case 'apireference':
      return <ApiReferenceSection />;
    case 'dataformats':
      return <DataFormatsSection />;
    case 'maintainingqualitydata':
      return <MaintainingQualityDataSection />;
    case 'casestudies':
      return <CaseStudiesSection />;
    case 'help':
      return <HelpSection supportEmail={config.supportEmail} />;
    default:
      return <OverviewSection />;
  }
}

function PaginationNav({ currentSection }: { currentSection: string }) {
  const currentIndex = SECTIONS.findIndex((s) => s.name === currentSection);
  const prevSection = currentIndex > 0 ? SECTIONS[currentIndex - 1] : null;
  const nextSection = currentIndex >= 0 && currentIndex < SECTIONS.length - 1 ? SECTIONS[currentIndex + 1] : null;

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

function DeveloperDocumentationContent() {
  const searchParams = useSearchParams();
  const section = searchParams.get('section') || 'overview';

  return (
    <div className="govuk-width-container">
      <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/">Bus Open Data Service</Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/data">Find Bus Open Data</Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/publish/guide-me">Guide Me</Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            Developer documentation
          </li>
        </ol>
      </nav>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Developer documentation</h1>
            <ul className="govuk-body dashed">
              {SECTIONS.map((s) => (
                <li key={s.name} className="govuk-!-padding-bottom-1">
                  <Link className={`govuk-link ${s.name === section ? 'govuk-!-font-weight-bold' : ''}`} href={`?section=${s.name}`}>
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
            <h2 className="govuk-heading-s">Other development resources</h2>
            <ul className="govuk-list">
              <li>
                <a className="govuk-link" href="https://github.com/department-for-transport-BODS/bods" target="_blank" rel="noopener noreferrer">
                  Github repo
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DeveloperDocumentationPage() {
  return (
    <Suspense fallback={<div className="govuk-width-container"><p className="govuk-body">Loading...</p></div>}>
      <DeveloperDocumentationContent />
    </Suspense>
  );
}

