/**
 * Dataset Detail Page
 * 
 * 
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/index.html
 * View: transit_odp/browse/views/timetable_views.py - DatasetDetailView
 * 
 * Server Component for optimal SEO and initial data fetch
 */

import { notFound } from 'next/navigation';
import { headers } from 'next/headers';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { DatasetDetailContent } from '@/components/data/DatasetDetailContent';
import type { Dataset } from '@/types';
import { HOSTS } from '@/config/client';
import { serverConfig } from '@/config/server';

interface DatasetDetailPageProps {
  params: Promise<{ id: string }>;
}

function formatDatasetTimestamp(dateString: string): string {
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/London',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  const parts = formatter.formatToParts(new Date(dateString));
  const getPart = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? '';

  return `${getPart('day')} ${getPart('month')} ${getPart('year')} ${getPart('hour')}:${getPart('minute')}`;
}

/**
 * Fetch dataset from Django API (server-side)
 */
async function getDataset(id: string): Promise<Dataset | null> {
  try {
    const url = new URL(
      `/api/v1/dataset/${encodeURIComponent(id)}/`,
      serverConfig.djangoInternalOrigin,
    );
    const requestHeaders = await headers();
    const upstreamHeaders = new Headers();
    const cookie = requestHeaders.get('cookie');
    if (cookie) {
      upstreamHeaders.set('cookie', cookie);
    }
    const dataHost = new URL(HOSTS.data).host;
    upstreamHeaders.set('host', dataHost);
    upstreamHeaders.set('x-forwarded-host', dataHost);

    const response = await fetch(url, {
      method: 'GET',
      headers: upstreamHeaders,
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      console.error(`Failed to fetch dataset: ${response.status} ${response.statusText}`);
      return null;
    }

    const data = await response.json();
    return data as Dataset;
  } catch (error) {
    console.error('Error fetching dataset:', error);
    return null;
  }
}

export default async function DatasetDetailPage({ params }: DatasetDetailPageProps) {
  const { id } = await params;
  
  const dataset = await getDataset(id);

  if (!dataset) {
    notFound();
  }

  const formattedLastUpdated = formatDatasetTimestamp(dataset.modified);

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Home', href: '/' },
          { label: 'Browse', href: '/data' },
          { label: 'Timetables Data', href: '/data?status=live' },
          { label: dataset.name, current: true, truncateAt: 19 },
        ]}
      />

      <main className="govuk-main-wrapper" id="main-content" role="main">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l app-mb-4 dont-break-out">
              {dataset.name}
            </h1>
            <p className="govuk-body app-mb-sm-0">
              Overview of the available bus open data
            </p>
          </div>
        </div>

        <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <DatasetDetailContent
              dataset={dataset}
              formattedLastUpdated={formattedLastUpdated}
              mapboxToken={serverConfig.mapboxToken}
            />
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">What you need to know</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <Link href="/guidance/support/developer" className="govuk-link">
                  View developer documentation
                </Link>
              </li>
              <li>
                <a
                  className="govuk-link"
                  href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Find out more about bus open data
                </a>
              </li>
              <li>
                <Link href="/contact" className="govuk-link">
                  Contact us for technical issues
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

/**
 * Generate metadata for the page
 */
export async function generateMetadata({ params }: DatasetDetailPageProps) {
  const { id } = await params;
  const dataset = await getDataset(id);

  if (!dataset) {
    return {
      title: 'Dataset Not Found - Bus Open Data Service',
    };
  }

  return {
    title: `${dataset.name} - Bus Open Data Service`,
    description: dataset.description || `View details for ${dataset.name} dataset`,
  };
}
