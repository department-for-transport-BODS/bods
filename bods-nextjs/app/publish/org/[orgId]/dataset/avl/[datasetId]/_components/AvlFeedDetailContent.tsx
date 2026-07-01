'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api-client';
import { AvlFeedDetailTable } from './AvlFeedDetailTable';
import { AvlCompliancePanels } from './AvlCompliancePanels';
import { AvlFeedDetailSidebar } from './AvlFeedDetailSidebar';
import { AvlFeedDetailActions } from './AvlFeedDetailActions';

export interface AvlFeedDetail {
  datasetId: number;
  name: string;
  description: string;
  shortDescription: string;
  status: string;
  organisationName: string;
  organisationId: number;
  siriVersion: string;
  urlLink: string;
  lastModified: string;
  lastModifiedUser?: string;
  lastServerUpdate: string;
  publishedBy?: string;
  publishedAt: string;
  avlComplianceStatus: string;
  avlTimetablesMatching?: string;
  isDummy: boolean;
}

export function AvlFeedDetailContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [feedDetail, setFeedDetail] = useState<AvlFeedDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let isCancelled = false;

    const fetchFeedDetail = async () => {
      setIsLoading(true);
      setError('');

      try {
        const response = await api.get<AvlFeedDetail>(
          `/api/avl/detail/${orgId}/${datasetId}/`,
        );
        if (!isCancelled) {
          setFeedDetail(response);
        }
      } catch (err) {
        if (!isCancelled) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to load feed details';
          setError(errorMsg);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchFeedDetail();

    return () => {
      isCancelled = true;
    };
  }, [orgId, datasetId]);

  if (isLoading) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <p className="govuk-body">Loading feed details...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !feedDetail) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <div className="govuk-error-summary" role="alert">
                <h2 className="govuk-error-summary__title">Unable to load feed details</h2>
                <div className="govuk-error-summary__body">
                  <p className="govuk-body">{error || 'Feed not found'}</p>
                  <Link className="govuk-link" href={`/publish/org/${orgId}/dataset/avl`}>
                    Back to feeds
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const breadcrumbName =
    feedDetail.name.length > 20 ? `${feedDetail.name.slice(0, 19)}...` : feedDetail.name;

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
            <Link className="govuk-breadcrumbs__link" href="/publish/">
              Publish Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset/avl`}>
              Review My Bus Location Data
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset/avl/${datasetId}`}>
              {breadcrumbName}
            </Link>
          </li>
        </ol>
      </nav>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">{feedDetail.name}</h1>
            <p className="govuk-body">Preview your service data status and make changes</p>

            <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible" />

            {/* Compliance panels - conditional rendering */}
            <AvlCompliancePanels feedDetail={feedDetail} orgId={orgId} datasetId={datasetId} />

            {/* Main property table */}
            <AvlFeedDetailTable feedDetail={feedDetail} orgId={orgId} />

            {/* Action buttons */}
            <AvlFeedDetailActions feedDetail={feedDetail} orgId={orgId} datasetId={datasetId} />
          </div>

          {/* Sidebar */}
          <div className="govuk-grid-column-one-third govuk-!-padding-top-5">
            <AvlFeedDetailSidebar />
          </div>
        </div>
      </div>
    </div>
  );
}
