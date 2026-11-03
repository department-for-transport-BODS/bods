/**
 * Main column of the timetable dataset detail page (success content or the
 * "Data set not available" error panel).
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/
 *         {success_content,property_table,error_panel,feedback_content}.html
 */

import Link from 'next/link';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { datasetListPath, datasetSubpagePath } from '@/lib/dataset-paths';
import { DatasetApiUrlPanel } from './DatasetApiUrlPanel';
import { DatasetErrorPanel } from './DatasetErrorPanel';
import { DatasetFeedbackSection } from './DatasetFeedbackSection';
import { DatasetPropertyTable } from './DatasetPropertyTable';
import { DatasetSubscribeDownload } from './DatasetSubscribeDownload';
import { TimetableDataQualityRow } from './TimetableDataQualityRow';
import { TimetableServiceNumbers } from './TimetableServiceNumbers';
import type { TimetableDatasetDetail } from './types';

interface TimetableDatasetDetailContentProps {
  dataset: TimetableDatasetDetail;
  /** django-waffle `is_specific_feedback` */
  isSpecificFeedback: boolean;
}

function ErrorPanel({ dataset }: { dataset: TimetableDatasetDetail }) {
  const downloadHref = datasetSubpagePath('TIMETABLE', dataset.id, 'download');

  // Django only fills the link for expired / inactive datasets (and the
  // `get_working` variant for errored ones); otherwise the href is empty.
  let previousDataHref = '';
  if (dataset.status === 'expired' || dataset.status === 'inactive') {
    previousDataHref = downloadHref;
  } else if (dataset.status === 'error') {
    previousDataHref = `${downloadHref}?get_working=true`;
  }

  return (
    <DatasetErrorPanel
      heading="Data set not available"
      name={dataset.name}
      organisationName={dataset.organisationName}
      lastUpdated={dataset.lastUpdated}
      publishedBy={dataset.publishedBy}
      transxchangeVersion={dataset.transxchangeVersion}
      changelogHref={datasetSubpagePath('TIMETABLE', dataset.id, 'changelog')}
      previousDataHref={previousDataHref}
      feedbackHref={datasetSubpagePath('TIMETABLE', dataset.id, 'feedback')}
    />
  );
}

function SuccessContent({ dataset, isSpecificFeedback }: TimetableDatasetDetailContentProps) {
  return (
    <>
      <MapboxRouteMap revisionId={dataset.revisionId} />
      <DatasetPropertyTable
        id={dataset.id}
        name={dataset.name}
        dataTypeLabel="Timetables data"
        datasetType="TIMETABLE"
        description={dataset.description}
        organisationName={dataset.organisationName}
        ownerHref={datasetListPath('TIMETABLE', {
          organisation: dataset.organisationId,
          status: 'live',
        })}
        status={dataset.status}
      >
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            TransXChange version
          </th>
          <td className="govuk-table__cell" colSpan={2}>
            {dataset.transxchangeVersion}
          </td>
        </tr>
        {dataset.dataQuality ? (
          <TimetableDataQualityRow
            dataQuality={dataset.dataQuality}
            organisationId={dataset.organisationId}
            datasetId={dataset.id}
            isSpecificFeedback={isSpecificFeedback}
          />
        ) : null}
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Last updated
          </th>
          <td className="govuk-table__cell dont-break-out">{dataset.lastUpdated}</td>
          <td className="govuk-table__cell">
            <Link className="govuk-link" href={datasetSubpagePath('TIMETABLE', dataset.id, 'changelog')}>
              View change log
            </Link>
          </td>
        </tr>
      </DatasetPropertyTable>
      <TimetableServiceNumbers datasetId={dataset.id} licences={dataset.serviceNumbers} />
      {dataset.feedApi ? <DatasetApiUrlPanel apiUrl={dataset.feedApi} datasetType="TIMETABLE" /> : null}
      <DatasetSubscribeDownload
        datasetId={dataset.id}
        datasetType="TIMETABLE"
        isSubscribed={dataset.isSubscribed}
        fileExtension={dataset.uploadFileExtension}
      />
      {isSpecificFeedback ? null : <DatasetFeedbackSection datasetId={dataset.id} datasetType="TIMETABLE" />}
    </>
  );
}

export function TimetableDatasetDetailContent(props: TimetableDatasetDetailContentProps) {
  return props.dataset.error ? <ErrorPanel dataset={props.dataset} /> : <SuccessContent {...props} />;
}
