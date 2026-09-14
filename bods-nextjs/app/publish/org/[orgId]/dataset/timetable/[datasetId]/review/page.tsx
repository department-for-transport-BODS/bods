'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { PublishStepper } from '@/components/publish';
import { formatDateTime } from '@/lib/utils/date';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import { TimetableHelpAside } from '../../_components/TimetableHelpAside';
import { TimetableReviewMap } from '../../_components/TimetableReviewMap';

type TimetableMetadata = {
  filename?: string;
  serviceCode?: string;
  nationalOperatorCode?: string;
  lineNames?: string;
  origin?: string;
  destination?: string;
  operatingPeriodStartDate?: string | null;
  operatingPeriodEndDate?: string | null;
  schemaVersion?: string;
  revisionNumber?: string;
  modification?: string;
  serviceMode?: string;
};

type TimetableReviewStatusResponse = {
  datasetId: number;
  revisionId: number;
  status: string;
  progress: number;
  loading: boolean;
  name?: string;
  description?: string;
  shortDescription?: string;
  urlLink?: string;
  ownerName?: string;
  downloadUrl?: string;
  lastModified?: string;
  lastModifiedUser?: string;
  metadata?: TimetableMetadata[];
  error?: string | null;
  errorDescription?: string | null;
  validationState?: 'passed' | 'passed-with-issues' | 'failed';
  validationReportUrl?: string;
  hasSchemaViolation?: boolean;
  hasPostSchemaViolation?: boolean;
  hasPtiObservations?: boolean;
  transxchangeVersion?: string | null;
  publisherUrl?: string | null;
  distinctAttributes?: Record<string, Record<string, Record<string, string[]>>>;
  dataQuality?: {
    status: string;
    score?: number | null;
    ragLevel?: string | null;
    criticalCount?: number;
    advisoryCount?: number;
    reportUrl?: string;
    reportCsvUrl?: string | null;
    showUpdate?: boolean;
  };
};

type PublishResponse = {
  redirect?: string;
  published?: boolean;
};

function TimetableReviewPageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const timetablesListUrl = `/publish/org/${orgId}/dataset/timetable`;

  const {
    statusData,
    processingProgress,
    errorMessage,
    setErrorMessage,
  } = useDatasetReview<TimetableReviewStatusResponse>(
    datasetId,
    `/api/publish/timetables/review-status/${orgId}/${datasetId}/`,
  );
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);

  const handlePublish = async () => {
    if (isPublishing) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const data = await api.post<PublishResponse>(`/api/publish/timetables/publish/${orgId}/${datasetId}/`);
      globalThis.location.href = data.redirect || timetablesListUrl;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An error occurred while publishing.';
      setErrorMessage(message);
      setIsPublishing(false);
    }
  };

  const loading = statusData?.loading ?? true;
  const progress = Math.max(
    0,
    Math.min(100, statusData?.progress ?? processingProgress),
  );
  const hasValidationIssues = statusData?.validationState === 'passed-with-issues';
  const dataQuality = statusData?.dataQuality;
  const noValidFile = statusData?.error === 'NO_VALID_FILE_TO_PROCESS';

  const updateUrl = `/publish/org/${orgId}/dataset/timetable/new?step=provide-data`;
  const deleteUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}/delete`;

  const renderValidationPanel = () => {
    return (
      <section className="timetable-review-panel">
        <h2 className="govuk-heading-m">
          3a Validation check - {hasValidationIssues ? 'Passed with issues' : 'Passed'}
        </h2>
        {hasValidationIssues ? (
          <>
            <p className="govuk-body">The validation report checks for compliance against the mandated TxC 2.4 v1.1 profile.</p>
            <a className="govuk-link" href={statusData?.validationReportUrl}>Download validation report</a>
            <p className="govuk-body">Some of the files in the data supplied are non-compliant and cannot be submitted to BODS as per the guidance. To pass the validation please address all outstanding issues in the validation report.</p>
          </>
        ) : null}
      </section>
    );
  };

  const renderDataQualityPanel = () => {
    if (!dataQuality || dataQuality.status === 'PENDING') {
      return (
        <section className="timetable-review-panel">
          <p className="govuk-body">Your data set has been uploaded as a draft.</p>
          <p className="govuk-body">A data quality report is being generated.</p>
          <p className="govuk-body">You can wait or close the browser. You can publish your data once the report is ready.</p>
        </section>
      );
    }
    if (dataQuality.status === 'FAILURE') {
      return (
        <section className="timetable-review-panel timetable-review-panel--error">
          <h2 className="govuk-heading-m">Supplied data set has failed to upload</h2>
          <p className="govuk-body">The data quality service is currently unavailable, please try again later.</p>
          <Link className="govuk-link" href="/contact">Contact support</Link>
          <br />
          <Link className="govuk-button govuk-button--secondary" href={updateUrl}>Update data</Link>
          <Link className="govuk-button govuk-button--secondary" href={deleteUrl}>Delete data</Link>
        </section>
      );
    }
    return (
      <section className="timetable-review-panel">
        <h2 className="govuk-heading-m">
          3b Data quality check{dataQuality.ragLevel ? ` - ${dataQuality.ragLevel}` : ''}
        </h2>
        <p className="govuk-body">The data quality report identifies data quality issues beyond the validation checks. Please review any raised issues.</p>
        <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={dataQuality.reportUrl}>View data quality report</a>
        {dataQuality.reportCsvUrl ? (
          <>
            <br />
            <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={dataQuality.reportCsvUrl}>Download data quality report.csv</a>
          </>
        ) : null}
        <table className="govuk-table govuk-!-margin-top-2">
          <tbody className="govuk-table__body">
            <tr className="govuk-table__row"><td className="govuk-table__cell">{dataQuality.criticalCount || 0}</td><td className="govuk-table__cell">Critical data quality observations</td></tr>
            <tr className="govuk-table__row"><td className="govuk-table__cell">{dataQuality.advisoryCount || 0}</td><td className="govuk-table__cell">Advisory data quality observations</td></tr>
          </tbody>
        </table>
        {dataQuality.showUpdate ? <Link className="govuk-button govuk-button--secondary" href={updateUrl}>Update data</Link> : null}
      </section>
    );
  };

  const renderNoValidFileState = () => (
    <>
      <section className="timetable-review-panel">
        <h2 className="govuk-heading-m">Validation check - Failed</h2>
        <p className="govuk-body">The validation report checks for compliance against the mandated TxC 2.4 v1.1 profile.</p>
        <a className="govuk-link" href={statusData?.validationReportUrl}>Download validation report</a>
        <p className="govuk-body">The timetables data supplied is non-compliant and cannot be submitted to BODS. To pass the validation please address all outstanding issues in the validation report.</p>
      </section>
      <Link className="govuk-button govuk-!-margin-top-3" href={updateUrl}>Update data</Link>
      <Link className="govuk-button govuk-button--secondary govuk-!-margin-top-3 govuk-!-margin-left-2" href={deleteUrl}>Delete data</Link>
      <h2 className="govuk-heading-l govuk-!-padding-top-5">{statusData?.name || 'Timetable data set'}</h2>
      <dl className="govuk-summary-list">
        <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Name</dt><dd className="govuk-summary-list__value">{statusData?.name || '-'}</dd></div>
        <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Owner</dt><dd className="govuk-summary-list__value">{statusData?.ownerName || '-'}</dd></div>
        <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Last updated</dt><dd className="govuk-summary-list__value">by System</dd></div>
      </dl>
    </>
  );

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <PublishStepper
          steps={[
            { label: '1. Describe data', state: 'previous' },
            { label: '2. Provide data', state: loading ? 'selected' : 'previous' },
            { label: '3. Review and publish', state: loading ? 'next' : 'selected' },
          ]}
        />
      </div>

      <div className="govuk-main-wrapper">
        <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="timetable-review-error-title" />

        {!loading && (
          <>
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <h1 className="govuk-heading-xl">Review and publish</h1>
              </div>
            </div>
            <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
          </>
        )}

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {statusData?.loading ? (
              <div className="govuk-panel govuk-panel--confirmation timetable-validation-panel">
                <h1 className="govuk-panel__title govuk-!-font-size-36">Validating data sets</h1>
                <div className="govuk-panel__body govuk-!-font-size-19">
                  <div className="pb3-l">
                    <p>Once successfully processed, the data set will be published, and you will be able to view the details here.</p>
                    <p>Please expect a temporary delay in processing time as we work to bring you new and enhanced features.</p>
                  </div>
                  <div id="progressOuterDiv" className="progress-bar-outer">
                    <div id="progressInnerDiv" className="progress-bar-inner" style={{ width: `${progress}%` }} />
                  </div>
                  <span id="progressSpan" className="progress-bar-text">{progress}%</span>
                </div>
              </div>
            ) : statusData === null ? null : noValidFile ? (
              renderNoValidFileState()
            ) : statusData?.error ? (
              <>
                <h2 className="govuk-heading-l govuk-!-padding-top-5">{statusData.name || 'Timetable data set'}</h2>
                <ErrorSummary
                  errors={[statusData.errorDescription || 'Something went wrong and we could not process your data set. Please try again later.']}
                  title="Supplied data set has failed to upload"
                  summaryId="timetable-upload-error-title"
                  className="govuk-!-margin-bottom-0"
                  titleClassName="govuk-!-margin-bottom-2"
                  itemClassName="app-error-summary__item"
                  tabIndex={-1}
                />
                <div className="govuk-!-padding-bottom-7 govuk-!-padding-top-5">
                  <Link className="govuk-button" href={updateUrl}>Publish correct data set</Link>
                </div>
                <dl className="govuk-summary-list">
                  <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Name</dt><dd className="govuk-summary-list__value">{statusData.name || '-'}</dd></div>
                  <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Owner</dt><dd className="govuk-summary-list__value">{statusData.ownerName || '-'}</dd></div>
                  <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Last updated</dt><dd className="govuk-summary-list__value">by System</dd></div>
                </dl>
                <h3 className="govuk-heading-m">What should I do next?</h3>
                <p className="govuk-body">You can re-upload a different dataset file again. Please ensure that your provided data format is correct and that your dataset file contains valid data.</p>
                <p className="govuk-body app-!-text-muted govuk-!-font-size-19">Accepted file formats include .xml (TransXChange).</p>
                <Link className="govuk-button govuk-button--secondary" href={deleteUrl}>Delete data</Link>
              </>
            ) : (
              <>
                {renderValidationPanel()}
                {renderDataQualityPanel()}
                <h2 className="govuk-heading-l">{statusData?.name || 'Timetable data set'}</h2>
                {statusData?.revisionId ? <TimetableReviewMap revisionId={statusData.revisionId} /> : null}
                <dl className="govuk-summary-list">
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Name</dt>
                    <dd className="govuk-summary-list__value">{statusData?.name || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Description</dt>
                    <dd className="govuk-summary-list__value">{statusData?.description || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Short description</dt>
                    <dd className="govuk-summary-list__value">{statusData?.shortDescription || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Status</dt>
                    <dd className="govuk-summary-list__value">{statusData?.status || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Owner</dt>
                    <dd className="govuk-summary-list__value">{statusData?.ownerName || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">TransXChange version</dt>
                    <dd className="govuk-summary-list__value">{statusData?.transxchangeVersion || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">URL link</dt>
                    <dd className="govuk-summary-list__value">{statusData?.publisherUrl ? <a className="govuk-link" href={statusData.publisherUrl}>Publisher URL</a> : '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Last modified</dt>
                    <dd className="govuk-summary-list__value">{formatDateTime(statusData?.lastModified)}</dd>
                  </div>
                </dl>

                {statusData?.distinctAttributes ? (
                  <>
                    <h2 className="govuk-heading-l">Review Service Numbers</h2>
                    <div className="govuk-accordion">
                      {Object.entries(statusData.distinctAttributes).map(([licence, nocs]) => (
                        <details className="govuk-details" key={licence}>
                          <summary className="govuk-details__summary"><span className="govuk-details__summary-text">{licence}</span></summary>
                          <div className="govuk-details__text">
                            {Object.entries(nocs).map(([noc, lines]) => (
                              <div key={noc}>
                                <h3 className="govuk-heading-s">{noc}</h3>
                                {Object.entries(lines).map(([line, serviceCodes]) => serviceCodes.map((serviceCode) => <p className="govuk-body" key={`${line}-${serviceCode}`}><a className="govuk-link" href={`/publish/org/${orgId}/dataset/timetable/${datasetId}/review/detail?line=${encodeURIComponent(line)}&revision_id=${statusData.revisionId}&service=${encodeURIComponent(serviceCode)}`}>{line} - {serviceCode}</a></p>))}
                              </div>
                            ))}
                          </div>
                        </details>
                      ))}
                    </div>
                  </>
                ) : null}

                {statusData?.metadata && statusData.metadata.length > 0 ? (
                  <>
                    <h2 className="govuk-heading-m">Detected services</h2>
                    <table className="govuk-table">
                      <thead className="govuk-table__head">
                        <tr className="govuk-table__row">
                          <th className="govuk-table__header">Filename</th>
                          <th className="govuk-table__header">Service code</th>
                          <th className="govuk-table__header">Line names</th>
                        </tr>
                      </thead>
                      <tbody className="govuk-table__body">
                        {statusData.metadata.map((item, index) => (
                          <tr key={`${item.filename || 'file'}-${index}`} className="govuk-table__row">
                            <td className="govuk-table__cell">{item.filename || '-'}</td>
                            <td className="govuk-table__cell">{item.serviceCode || '-'}</td>
                            <td className="govuk-table__cell">{item.lineNames || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                ) : null}

                <div className="govuk-form-group">
                  <div className="govuk-checkboxes__item">
                    <input
                      className="govuk-checkboxes__input"
                      id="id_has_reviewed"
                      type="checkbox"
                      checked={hasReviewed}
                      onChange={(event) => setHasReviewed(event.target.checked)}
                    />
                    <label className="govuk-label govuk-checkboxes__label" htmlFor="id_has_reviewed">
                      I have reviewed the data quality report and wish to publish my data
                    </label>
                  </div>
                </div>

                <div className="govuk-button-group">
                  <button
                    type="button"
                    className="govuk-button"
                    disabled={!hasReviewed || isPublishing || loading}
                    onClick={handlePublish}
                  >
                    {isPublishing ? 'Publishing...' : 'Publish'}
                  </button>
                  <Link className="govuk-link" href={timetablesListUrl}>
                    Back to data sets
                  </Link>
                </div>
                <Link className="govuk-button govuk-button--secondary" href={deleteUrl}>
                  Delete data
                </Link>
              </>
            )}
          </div>

          <TimetableHelpAside />
        </div>
      </div>
    </div>
  );
}

export default function TimetableReviewPage() {
  return (
    <ProtectedRoute>
      <TimetableReviewPageContent />
    </ProtectedRoute>
  );
}