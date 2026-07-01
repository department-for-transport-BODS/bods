'use client';

import Link from 'next/link';
import { AvlFeedDetail } from './AvlFeedDetailContent';
import { statusIndicatorClass, statusLabel } from '../../_components/avlStatus';
import { AvlMatchingHelpModal } from '@/components/publish/AvlMatchingHelpModal';
import { formatDateTime } from '@/lib/utils/date';

interface AvlFeedDetailTableProps {
  feedDetail: AvlFeedDetail;
  orgId: string;
}

export function AvlFeedDetailTable({ feedDetail, orgId }: AvlFeedDetailTableProps) {
  const editUrl = `/publish/org/${orgId}/dataset/avl/${feedDetail.datasetId}/update`;

  return (
    <table className="govuk-table dataset-property-table">
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Name
          </th>
          <td className="govuk-table__cell govuk-!-padding-3 dont-break-out">
            {feedDetail.name}
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Data feed ID
          </th>
          <td className="govuk-table__cell govuk-!-padding-3 dont-break-out">
            {feedDetail.datasetId}
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            URL link
          </th>
          <td className="govuk-table__cell govuk-!-padding-3 dont-break-out">
            {feedDetail.urlLink}
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Description
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            <div className="flex-between">
              <span className="dont-break-out">{feedDetail.description}</span>
              {!feedDetail.isDummy && (
                <span className="right-justify">
                  <Link className="govuk-link" href={editUrl}>
                    Edit
                  </Link>
                </span>
              )}
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Short description
          </th>
          <td className="govuk-table__cell govuk-!-padding-3 dont-break-out">
            <div className="flex-between">
              {feedDetail.shortDescription}
              {!feedDetail.isDummy && (
                <Link className="govuk-link" href={editUrl}>
                  Edit
                </Link>
              )}
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Status
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            <div className="flex-between">
              <span className={statusIndicatorClass(feedDetail.status)}>
                {statusLabel(feedDetail.status)}
              </span>
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            AVL to Timetables feed matching
            <AvlMatchingHelpModal variant="feed" />
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            <div className="stacked">
              <AvlTimetableMatchingSection matching={feedDetail.avlTimetablesMatching} />
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Owner
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            {feedDetail.organisationName}
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            SIRI-VM version
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            {feedDetail.siriVersion || '_'}
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Feed details last updated
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            <div className="flex-between">
              <span>
                {formatDateTime(feedDetail.publishedAt)}
                {' by '}
                {feedDetail.publishedBy || 'System'}
              </span>
              <span className="right-justify">
                <Link className="govuk-link" href={`/publish/org/${orgId}/dataset/avl/${feedDetail.datasetId}/changelog`}>
                  View change log
                </Link>
              </span>
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Last automated update
          </th>
          <td className="govuk-table__cell govuk-!-padding-3">
            {feedDetail.lastServerUpdate}
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function AvlTimetableMatchingSection({ matching }: { matching?: string }) {
  return (
    <p className="govuk-body govuk-!-margin-bottom-0">
      {!matching || matching === '0%' ? (
        <>
          <i className="fas fa-exclamation-circle fa"></i>
          {' Pending '}
        </>
      ) : (
        <>
          {matching !== '100%' && <i className="fas fa-exclamation-circle fa"></i>}
          {matching} completely matched AVL to Timetables
        </>
      )}
    </p>
  );
}
