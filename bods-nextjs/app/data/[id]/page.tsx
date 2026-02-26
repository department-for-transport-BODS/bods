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
import Link from 'next/link';
import { DatasetDetailContent } from '@/components/data/DatasetDetailContent';
import type { Dataset } from '@/types';

interface DatasetDetailPageProps {
  params: Promise<{ id: string }>;
}

/**
 * Fetch dataset from Django API (server-side)
 */
async function getDataset(id: string): Promise<Dataset | null> {
  try {
    const apiUrl = process.env.DJANGO_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
    const url = `${apiUrl}/api/v1/dataset/${id}/`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      next: { revalidate: 300 },
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

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link href="/" className="govuk-breadcrumbs__link">
              Home
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link href="/data" className="govuk-breadcrumbs__link">
              Browse
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link href="/data?status=live" className="govuk-breadcrumbs__link">
              Timetables Data
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            {dataset.name.length > 19 ? `${dataset.name.substring(0, 16)}...` : dataset.name}
          </li>
        </ol>
      </div>

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
            <DatasetDetailContent dataset={dataset} />
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
