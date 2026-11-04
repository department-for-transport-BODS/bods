/**
 * Main column of the AVL dataset detail page.
 *
 * Source: transit_odp/browse/templates/browse/avl/feed_detail/
 *         {success_content,property_table}.html,
 *         transit_odp/avl/templates/avl/snippets/avl_timetable_matching.html and
 *         transit_odp/publish/templates/publish/snippets/help_modals/AVL_timetables_feed_matching.html
 *
 * Django's AVL detail view never sets `error`, so (unlike timetables and
 * fares) there is no error panel: every status renders the success content.
 */

import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleExclamation } from '@fortawesome/free-solid-svg-icons';
import { publishPath } from '@/config/client';
import { datasetListPath, datasetSubpagePath } from '@/lib/dataset-paths';
import { DatasetApiUrlPanel } from './DatasetApiUrlPanel';
import { DatasetFeedbackSection } from './DatasetFeedbackSection';
import { DatasetHelpModal } from './DatasetHelpModal';
import { DatasetPropertyTable } from './DatasetPropertyTable';
import { DatasetSubscribeDownload } from './DatasetSubscribeDownload';
import type { AvlDatasetDetail } from './types';

interface AvlDatasetDetailContentProps {
  dataset: AvlDatasetDetail;
}

/** Django's `{% if not properties.avl_timetables_matching %}`: only null / "" is pending. */
function AvlTimetableMatching({ dataset }: AvlDatasetDetailContentProps) {
  const matching = dataset.avlTimetablesMatching;
  const matchingReportHref = publishPath(
    `/org/${dataset.organisationId}/dataset/avl/${dataset.id}/download-matching-report/`,
  );

  return (
    <>
      <p className="govuk-body govuk-!-margin-bottom-0">
        {matching !== '100%' ? <FontAwesomeIcon icon={faCircleExclamation} aria-hidden="true" /> : null}
        {matching ? ` ${matching} completely matched AVL to Timetables` : ' Pending'}
      </p>
      {matching ? (
        <a className="govuk-link govuk-!-margin-left-5 govuk-!-margin-top-1" href={matchingReportHref}>
          Download matching report
        </a>
      ) : null}
    </>
  );
}

export function AvlDatasetDetailContent({ dataset }: AvlDatasetDetailContentProps) {
  return (
    <>
      <DatasetPropertyTable
        id={dataset.id}
        name={dataset.name}
        dataTypeLabel="Bus location data"
        datasetType="AVL"
        description={dataset.description}
        organisationName={dataset.organisationName}
        ownerHref={datasetListPath('AVL', {
          organisation: dataset.organisationId,
          status: 'live',
        })}
        status={dataset.status}
      >
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            AVL to Timetables feed matching
            <DatasetHelpModal heading="AVL to Timetables feed sampled matching">
              <p className="govuk-body">
                The AVL to Timetables feed matching is a weekly score of a published data feed. Daily random
                samples of data packets are collected for each published feed to be matched and then collated
                together to create a weekly report along with a weekly associated summary score for that
                report. This is usually done on Monday every week.
              </p>
              <p className="govuk-body">This is the latest matching score for this feed.</p>
              <p className="govuk-body">
                Please note that BODS doesn&apos;t check every single packet of data but we do a random
                sampling throughout the day in order to determine these reports and scores.
              </p>
              <p className="govuk-body">
                Please download the report and work with your technology suppliers to provide the most
                accurate data so that download data consumers and eventually your bus passengers can benefit.
              </p>
            </DatasetHelpModal>
          </th>
          <td className="govuk-table__cell" colSpan={2}>
            <div className="stacked">
              <AvlTimetableMatching dataset={dataset} />
            </div>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            SIRI-VM version
          </th>
          <td className="govuk-table__cell" colSpan={2}>
            {dataset.siriVmVersion}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Feed details last updated
          </th>
          <td className="govuk-table__cell dont-break-out">{dataset.lastUpdated}</td>
          <td className="govuk-table__cell">
            <Link className="govuk-link" href={datasetSubpagePath('AVL', dataset.id, 'changelog')}>
              View change log
            </Link>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Last automated update
          </th>
          <td className="govuk-table__cell" colSpan={2}>
            {dataset.lastAutomatedUpdate}
          </td>
        </tr>
      </DatasetPropertyTable>
      {dataset.feedApi ? <DatasetApiUrlPanel apiUrl={dataset.feedApi} datasetType="AVL" /> : null}
      <DatasetSubscribeDownload
        datasetId={dataset.id}
        datasetType="AVL"
        isSubscribed={dataset.isSubscribed}
      />
      <DatasetFeedbackSection datasetId={dataset.id} datasetType="AVL" />
    </>
  );
}
