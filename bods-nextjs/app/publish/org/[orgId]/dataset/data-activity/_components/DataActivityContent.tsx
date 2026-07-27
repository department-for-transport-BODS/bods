'use client';

import { api } from '@/lib/api-client';
import { useParams, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

interface OrganisationStats {
  total_subscriptions: number;
  weekly_downloads: number;
  weekly_api_hits: number;
  weekly_unique_consumers: number;
}

export function DataActivityContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const prev = searchParams.get('prev');

  const [stats, setStats] = useState<OrganisationStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadStats = async () => {
      try {
        setIsLoading(true);
        const response = await api.get<OrganisationStats>(`/api/organisation/stats/${orgId}/`);
        setStats(response);
      } catch (err) {
        console.error('Error loading stats:', err);
        setError('Unable to load data activity statistics');
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, [orgId]);

  const getBacklinkUrl = (): string => {
    if (prev === 'avl-feed-list') {
      return `/publish/org/${orgId}/dataset/avl`;
    }
    if (prev === 'fares-feed-list') {
      return `/publish/org/${orgId}/dataset/fares`;
    }
    if (prev === 'timetable-feed-list') {
      return `/publish/org/${orgId}/dataset/timetable`;
    }
    return `/publish/org/${orgId}`;
  };

  const backlinkUrl = getBacklinkUrl();

  return (
    <>
      <div className="govuk-width-container">
        <a href={backlinkUrl} className="govuk-back-link">
          Back
        </a>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full govuk-!-margin-bottom-9">
              <div className="govuk-!-margin-bottom-6">
                <h1 className="govuk-heading-l">Data consumer activity</h1>
                <p className="govuk-body govuk-!-margin-bottom-6">
                  The statistics on this page are generated on a fixed time interval. It is aimed to provide a snapshot
                  of consumer activities relating to all your data (including timetables, bus location and fares).
                </p>
              </div>

              {isLoading && <p className="govuk-body">Loading data...</p>}
              {error && <p className="govuk-body govuk-error-message">{error}</p>}

              {!isLoading && stats && (
                <>
                  <h2 className="govuk-heading-s govuk-!-margin-top-3">Number of current active subscriptions</h2>
                  <div id="feed-stat-list" className="govuk-grid-row">
                    <div className="govuk-grid-column-one-quarter">
                      <div className="feed-stat">
                        <span className="feed-stat__value">{stats.total_subscriptions}</span>
                        <span className="feed-stat__label govuk-!-font-size-14">Subscriptions</span>
                      </div>
                    </div>
                  </div>

                  <h2 className="govuk-heading-s govuk-!-margin-top-4">
                    Number of total consumer interactions related to your data in the last 7 days
                  </h2>
                  <div id="feed-stat-list" className="govuk-grid-row">
                    <div className="govuk-grid-column-one-quarter">
                      <div className="feed-stat">
                        <span className="feed-stat__value">{stats.weekly_downloads}</span>
                        <span className="feed-stat__label govuk-!-font-size-14">Downloads</span>
                      </div>
                    </div>

                    <div className="govuk-grid-column-one-third">
                      <div className="feed-stat">
                        <span className="feed-stat__value">{stats.weekly_api_hits}</span>
                        <span className="feed-stat__label govuk-!-font-size-14">API hits</span>
                      </div>
                    </div>

                    <div className="govuk-grid-column-one-third">
                      <div className="feed-stat">
                        <span className="feed-stat__value">{stats.weekly_unique_consumers}</span>
                        <span className="feed-stat__label govuk-!-font-size-14">No. of Unique consumers</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="govuk-grid-column-one-half govuk-!-margin-bottom-2">
              <h2 className="govuk-heading-m">Data consumer interactions with your data since publishing</h2>
              <p className="govuk-body">
                This will include subscription, download, search results from browsing, and API hits.
              </p>
              <a className="govuk-link govuk-!-font-size-19" href={`/api/avl/consumer-interactions/${orgId}`}>
                Download report
              </a>

              <h2 className="govuk-heading-m govuk-!-margin-top-8">Data issues reported on published data</h2>
              <p className="govuk-body">
                This will provide you details of the data with issues that have been reported on and also the number of
                issues reported on each of them.
              </p>
              <a className="govuk-link govuk-!-font-size-19" href={`/api/avl/consumer-feedback/${orgId}`}>
                Download report
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
