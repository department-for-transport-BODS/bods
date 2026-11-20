/**
 * Main column of the fares dataset detail page (success content or the
 * "Data feed not available" error panel).
 *
 * Source: transit_odp/browse/templates/browse/fares/feed_detail/
 *         {success_content,property_table,error_panel,feedback_content}.html and
 *         transit_odp/publish/templates/publish/snippets/dataset_map.html
 */

import Link from 'next/link';
import { publishPath } from '@/config/client';
import { MapboxFaresStopMap } from '@/components/data/MapboxFaresStopMap';
import { datasetListPath, datasetSubpagePath } from '@/lib/dataset-paths';
import { DatasetApiUrlPanel } from './DatasetApiUrlPanel';
import { DatasetErrorPanel } from './DatasetErrorPanel';
import { DatasetFeedbackSection } from './DatasetFeedbackSection';
import { DatasetPropertyTable } from './DatasetPropertyTable';
import { DatasetSubscribeDownload } from './DatasetSubscribeDownload';
import type { FaresDatasetDetail } from './types';

interface FaresDatasetDetailContentProps {
  dataset: FaresDatasetDetail;
  /** django-waffle `is_fares_validator_active` */
  isFaresValidatorActive: boolean;
}

function FaresErrorPanel({ dataset }: { dataset: FaresDatasetDetail }) {
  // Django reuses the timetable download for fares; the panel only renders for
  // errored datasets, so the link is always the `get_working` variant.
  const previousDataHref = `${datasetSubpagePath('TIMETABLE', dataset.id, 'download')}?get_working=true`;

  return (
    <DatasetErrorPanel
      heading="Data feed not available"
      name={dataset.name}
      organisationName={dataset.organisationName}
      lastUpdated={dataset.lastUpdated}
      publishedBy={dataset.publishedBy}
      transxchangeVersion={dataset.transxchangeVersion}
      changelogHref={datasetSubpagePath('FARES', dataset.id, 'changelog')}
      previousDataHref={previousDataHref}
      feedbackHref={datasetSubpagePath('FARES', dataset.id, 'feedback')}
    />
  );
}

function CompliantRow({ dataset }: { dataset: FaresDatasetDetail }) {
  return (
    <tr className="govuk-table__row">
      <th scope="row" className="govuk-table__header">
        BODS Compliant data
      </th>
      <td colSpan={2} className="govuk-table__cell">
        {dataset.isCompliantError ? (
          <div className="govuk-warning-text stacked govuk-!-margin-bottom-0">
            <span className="govuk-warning-text__icon content-box" aria-hidden="true">
              !
            </span>
            <span className="app-step-nav-related_white-top-border app-task-list__items_bottom-padding">
              Non compliant
            </span>
            {dataset.showReportLink ? (
              <a
                className="govuk-link govuk-!-margin-left-6"
                href={publishPath(
                  `/org/${dataset.organisationId}/dataset/fares-validator/${dataset.revisionId}/export/`,
                )}
              >
                Download validation report
              </a>
            ) : null}
          </div>
        ) : (
          <span className="item__value">Compliant</span>
        )}
      </td>
    </tr>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <tr className="govuk-table__row">
      <th scope="row" className="govuk-table__header">
        {label}
      </th>
      <td className="govuk-table__cell" colSpan={2}>
        {value}
      </td>
    </tr>
  );
}

function SuccessContent({ dataset, isFaresValidatorActive }: FaresDatasetDetailContentProps) {
  const { metadata } = dataset;

  return (
    <>
      {/* Django always renders the container; the map is only started when `showMap` */}
      {dataset.showMap ? (
        <MapboxFaresStopMap revisionId={dataset.revisionId} />
      ) : (
        <div id="map" className="disruptions-width" />
      )}
      <DatasetPropertyTable
        id={dataset.id}
        name={dataset.name}
        dataTypeLabel="Fares data"
        datasetType="FARES"
        description={dataset.description}
        organisationName={dataset.organisationName}
        ownerHref={datasetListPath('FARES', {
          organisation: dataset.organisationId,
          status: 'live',
        })}
        status={dataset.status}
      >
        {isFaresValidatorActive ? <CompliantRow dataset={dataset} /> : null}
        <MetadataRow label="NeTEx Version" value={metadata.schemaVersion} />
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Last updated
          </th>
          <td className="govuk-table__cell dont-break-out">{dataset.lastUpdated}</td>
          <td className="govuk-table__cell">
            <Link className="govuk-link" href={datasetSubpagePath('FARES', dataset.id, 'changelog')}>
              View change log
            </Link>
          </td>
        </tr>
        <MetadataRow label="Number of fare zones" value={metadata.numOfFareZones} />
        <MetadataRow label="Number of lines" value={metadata.numOfLines} />
        <MetadataRow label="Number of sales offer packages" value={metadata.numOfSalesOfferPackages} />
        <MetadataRow label="Number of fare products" value={metadata.numOfFareProducts} />
        <MetadataRow label="Number of user types" value={metadata.numOfUserProfiles} />
        <MetadataRow label="Earliest start date" value={metadata.validFrom} />
        <MetadataRow label="Earliest end date" value={metadata.validTo} />
      </DatasetPropertyTable>
      {dataset.feedApi ? <DatasetApiUrlPanel apiUrl={dataset.feedApi} datasetType="FARES" /> : null}
      <DatasetSubscribeDownload
        datasetId={dataset.id}
        datasetType="FARES"
        isSubscribed={dataset.isSubscribed}
        fileExtension={dataset.uploadFileExtension}
      />
      <DatasetFeedbackSection datasetId={dataset.id} datasetType="FARES" />
    </>
  );
}

export function FaresDatasetDetailContent({
  dataset,
  isFaresValidatorActive,
}: FaresDatasetDetailContentProps) {
  if (dataset.status === 'error') {
    return <FaresErrorPanel dataset={dataset} />;
  }
  return <SuccessContent dataset={dataset} isFaresValidatorActive={isFaresValidatorActive} />;
}
