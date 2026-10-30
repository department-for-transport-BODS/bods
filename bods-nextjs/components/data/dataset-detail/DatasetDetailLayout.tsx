/**
 * Shared layout of the data-host dataset detail pages (timetable, AVL and
 * fares): breadcrumbs, heading block, visible rule, a two-thirds main
 * column and the "What you need to know" sidebar.
 *
 * Source: transit_odp/browse/templates/browse/{timetables/dataset_detail,avl/feed_detail,fares/feed_detail}/
 *         index.html, page_heading.html and related_links.html
 */

import type { ReactNode } from 'react';
import Link from 'next/link';
import { Breadcrumbs, type BreadcrumbItem } from '@/components/shared/Breadcrumbs';
import { dataPath, wwwPath } from '@/config/client';

interface DatasetDetailLayoutProps {
  breadcrumbs: BreadcrumbItem[];
  name: string;
  /**
   * AVL and fares page headings add `govuk-!-padding-bottom-3` to the h1 and
   * the intro line; the timetable heading does not.
   */
  paddedHeading?: boolean;
  children: ReactNode;
}

export function DatasetRelatedLinks() {
  return (
    <>
      <h2 className="govuk-heading-m">What you need to know</h2>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          <Link className="govuk-link" href={dataPath('/guidance/requirements')}>
            View developer documentation
          </Link>
        </li>
        <li>
          <a
            className="govuk-link"
            href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
            target="_blank"
          >
            Find out more about bus open data
          </a>
        </li>
        <li>
          <Link className="govuk-link" href={wwwPath('/contact')}>
            Contact us for technical issues
          </Link>
        </li>
      </ul>
    </>
  );
}

export function DatasetDetailLayout({
  breadcrumbs,
  name,
  paddedHeading = false,
  children,
}: DatasetDetailLayoutProps) {
  const padding = paddedHeading ? ' govuk-!-padding-bottom-3' : '';
  return (
    <div className="govuk-width-container">
      <Breadcrumbs items={breadcrumbs} />
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className={`govuk-heading-l app-!-mb-4${padding} dont-break-out`}>{name}</h1>
            <p className={`govuk-body app-!-mb-sm-0${padding}`}>Overview of the available bus open data</p>
          </div>
        </div>
        <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">{children}</div>
          <div className="govuk-grid-column-one-third">
            <DatasetRelatedLinks />
          </div>
        </div>
      </div>
    </div>
  );
}
