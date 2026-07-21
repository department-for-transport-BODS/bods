'use client';

import Link from 'next/link';
import { useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api-client';
import { useApiResource } from '@/hooks/useApiResource';
import { AvlFeedDetailTable } from './AvlFeedDetailTable';
import { AvlCompliancePanels } from './AvlCompliancePanels';
import { AvlFeedDetailSidebar } from './AvlFeedDetailSidebar';
import { AvlFeedDetailActions } from './AvlFeedDetailActions';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

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

  const fetchFeedDetail = useCallback(
    () => api.get<AvlFeedDetail>(`/api/avl/detail/${orgId}/${datasetId}/`),
    [datasetId, orgId],
  );

  const {
    data: feedDetail,
    isLoading,
    error,
  } = useApiResource<AvlFeedDetail>(fetchFeedDetail, 'Failed to load feed details');

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

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Bus Open Data Service', href: '/' },
          { label: 'Publish Bus Open Data', href: '/publish/' },
          {
            label: 'Review My Bus Location Data',
            href: `/publish/org/${orgId}/dataset/avl`,
          },
          {
            label: feedDetail.name,
            href: `/publish/org/${orgId}/dataset/avl/${datasetId}`,
            current: true,
            truncateAt: 20,
          },
        ]}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">{feedDetail.name}</h1>
            <p className="govuk-body">Preview your service data status and make changes</p>

            <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible" />

            {/* Compliance panels - conditional rendering */}
            <AvlCompliancePanels feedDetail={feedDetail} />

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
