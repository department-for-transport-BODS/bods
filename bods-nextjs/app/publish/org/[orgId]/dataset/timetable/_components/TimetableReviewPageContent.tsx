'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import { useParams } from 'next/navigation';
import { FormEvent, ReactNode, useEffect, useState } from 'react';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { PublishStepper } from '@/components/publish';
import { publishAppPath, wwwPath } from '@/config/client';
import { formatDateTime } from '@/lib/utils/date';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import { TimetableHelpAside } from './TimetableHelpAside';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';

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
    hasCriticalIssues?: boolean | null;
    reportId?: number | null;
    showUpdate?: boolean;
  };
};

type PublishResponse = {
  redirect?: string;
  published?: boolean;
};

const isDataQualityPending = (data: TimetableReviewStatusResponse) =>
  !data.error && (!data.dataQuality || data.dataQuality.status === 'PENDING');

type TimetableReviewPageContentProps = {
  /** Django `UpdateRevisionPublishView` (`update/review/`) instead of `PublishRevisionView` (`review/`). */
  isUpdate?: boolean;
};

const STEPPER_LABELS = {
  publish: ['1. Describe data', '2. Provide data', '3. Review and publish'],
  update: ['1. Comment', '2. Update', '3. Review and publish'],
} as const;

const DATA_QUALITY_CONSENT_LABEL = 'I have reviewed the data quality report and wish to publish my data';

/** Where to go after publishing: Django's UpdateRevisionPublishView uses `update/success`. */
export const getTimetablePublishRedirect = (
  { orgId, datasetId, isUpdate }: { orgId: string; datasetId: string; isUpdate: boolean },
  serverRedirect?: string,
) =>
  isUpdate
    ? publishAppPath(`/org/${orgId}/dataset/timetable/${datasetId}/update/success`)
    : serverRedirect || publishAppPath(`/org/${orgId}/dataset/timetable`);

/** Django `publish/snippets/pti_panel/base.html`. */
function PtiPanel({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <section>
      <div className="app-dqs-panel">
        <div className="app-dqs-panel__body">
          <div className="app-dqs-panel__success">{children}</div>
        </div>
      </div>
    </section>
  );
}

/** Django `publish/revision_review/delete_component.html`. */
function DeleteComponent({ deleteUrl }: Readonly<{ deleteUrl: string }>) {
  return (
    <>
      <h3 className="govuk-heading-m">What should I do next?</h3>
      <p className="govuk-body govuk-!-font-size-19">
        You can re-upload a different dataset file again. Please ensure that your provided data format is correct and
        that your dataset file contains valid data.
      </p>
      <p className="govuk-body app-!-text-muted govuk-!-font-size-19">
        Accepted file formats include .xml (TransXChange).
      </p>
      <div className="btn-group-justified">
        <a role="button" className="govuk-button govuk-button--secondary" href={deleteUrl}>Delete data</a>
      </div>
    </>
  );
}

/** Django `publish/snippets/error_summary_table.html`; a draft revision has no `published_at`/`published_by`. */
function ErrorSummaryTable({ name, ownerName }: Readonly<{ name: string; ownerName: string }>) {
  return (
    <table className="govuk-table dataset-property-table">
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Name</th>
          <td className="govuk-table__cell dont-break-out">{name}</td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Owner</th>
          <td className="govuk-table__cell">{ownerName}</td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Last updated</th>
          <td className="govuk-table__cell">
            <div className="flex-between"><span>by System</span></div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}

export function TimetableReviewPageContent({ isUpdate = false }: Readonly<TimetableReviewPageContentProps>) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;


  const {
    statusData,
    progress,
    isInitialLoading,
    errorMessage,
    setErrorMessage,
  } = useDatasetReview<TimetableReviewStatusResponse>(
    datasetId,
    `/api/publish/timetables/review-status/${orgId}/${datasetId}/`,
    'Unable to check processing status. Please refresh and try again.',
    '',
    {
      fetchReviewFirst: true,
      keepPollingReview: isDataQualityPending,
      reviewStatusPath: `/api/publish/timetables/data-quality-status/${orgId}/${datasetId}/`,
    },
  );
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);

  const handlePublish = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isPublishing) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const data = await api.post<PublishResponse>(`/api/publish/timetables/publish/${orgId}/${datasetId}/`);
      globalThis.location.href = getTimetablePublishRedirect({ orgId, datasetId, isUpdate }, data.redirect);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An error occurred while publishing.';
      setErrorMessage(message);
      setIsPublishing(false);
    }
  };

  const loading = statusData ? statusData.loading : !errorMessage;
  const pageTitle = loading
    ? 'Validating data set'
    : statusData?.error || errorMessage
      ? 'Error: Review and publish'
      : 'Review and publish';

  useEffect(() => {
    document.title = pageTitle;
  }, [pageTitle]);
  const hasValidationIssues = statusData?.validationState === 'passed-with-issues';
  const dataQuality = statusData?.dataQuality;
  const noValidFile = statusData?.error === 'NO_VALID_FILE_TO_PROCESS';

  const datasetPath = `/org/${orgId}/dataset/timetable/${datasetId}`;
  // Django links to `update-modify` (`update/review/update`) from the update review and
  // `upload-modify` from the first-publish review (served by `update/` in Next.js).
  const updateUrl = publishAppPath(isUpdate ? `${datasetPath}/update/review/update` : `${datasetPath}/update`);
  const stepperLabels = isUpdate ? STEPPER_LABELS.update : STEPPER_LABELS.publish;
  const deleteUrl = publishAppPath(`${datasetPath}/delete/`);
  const revisionEditUrl = publishAppPath(`${datasetPath}/revision-edit/`);
  const guidanceUrl = publishAppPath('/guidance/operator-requirements');
  const reportId = dataQuality?.reportId;
  const reportUrl = publishAppPath(`${datasetPath}/report/draft/`);
  const reportCsvUrl = reportId
    ? `/api/publish/timetables/data-quality-report/${orgId}/${datasetId}/${reportId}/csv/`
    : null;
  const name = statusData?.name || '';
  const ownerName = statusData?.ownerName || '';
  const criticalIssuesTag = dataQuality?.hasCriticalIssues == null ? null : (
    <span className={`govuk-tag govuk-tag--${dataQuality.hasCriticalIssues ? 'red' : 'green'} govuk-!-margin-left-3 govuk-!-font-size-16 govuk-!-text-align-centre`}>
      {dataQuality.hasCriticalIssues ? 'CRITICAL ISSUES' : 'NO CRITICAL ISSUES'}
    </span>
  );

  // Django `publish/snippets/pti_panel/{pass,soft_fail}.html`.
  const renderValidationPanel = () => (
    <PtiPanel>
      {hasValidationIssues ? (
        <>
          <h2 className="govuk-heading-m">Validation check - Passed with issues</h2>
          <p className="govuk-body">The validation report checks for compliance against the mandated TxC 2.4 v1.1 profile.</p>
          <p className="govuk-body">
            <a className="govuk-link" href={statusData?.validationReportUrl}>Download validation report</a>
          </p>
          <p className="govuk-body">
            Some of the files in the data supplied is non-compliant and cannot be submitted to BODS as per the{' '}
            <a href={`${guidanceUrl}?section=dataquality`} className="govuk-link">guidance</a>{' '}
            To pass the validation please address all outstanding issues in the validation report.
          </p>
        </>
      ) : (
        <h2 className="govuk-heading-m govuk-!-margin-bottom-0">3a Validation check - Passed</h2>
      )}
    </PtiPanel>
  );

  // Django `publish/snippets/dqs_review_panel.html`.
  const renderDataQualityPanel = () => {
    const dqStatus = dataQuality?.status ?? 'PENDING';
    const isFailure = dqStatus === 'FAILURE';
    const isSuccess = dqStatus === 'SUCCESS';
    return (
      <section id="dqs-review-section">
        <div className="app-dqs-panel">
          <div className="app-dqs-panel__body">
            {isFailure ? (
              <>
                <h2 className="govuk-error-summary__title">Supplied data set has failed to upload</h2>
                <p className="app-error-summary__item--no-decoration">
                  The data quality service is currently unavailable, please try again later.
                </p>
                <p className="app-error-summary__item--no-decoration">
                  {' If the problem continues, please '}
                  <a className="govuk-link" href={wwwPath('/contact')}>contact support</a>.
                </p>
              </>
            ) : isSuccess ? (
              <>
                <h2 className="govuk-heading-m">
                  3b Data quality check
                  {dataQuality?.ragLevel ? ` - ${dataQuality.ragLevel}` : null}
                  {reportId && criticalIssuesTag ? <> - <span className="shifted-tag-top-3">{criticalIssuesTag}</span></> : null}
                </h2>
                <p className="govuk-body">
                  The data quality report identifies data quality issues beyond the validation checks. Please review any raised issues.
                </p>
                <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={reportUrl}>View data quality report</a>
                {reportCsvUrl ? (
                  <>
                    <br />
                    <a className="govuk-link" target="_blank" href={reportCsvUrl}>Download data quality report.csv</a>
                  </>
                ) : null}
                <table className="govuk-table govuk-!-margin-top-2">
                  <tbody className="govuk-table__body">
                    <tr className="govuk-table__row"><td className="govuk-table__cell">{dataQuality?.criticalCount || 0}</td><td className="govuk-table__cell">Critical data quality observations</td></tr>
                    <tr className="govuk-table__row"><td className="govuk-table__cell">{dataQuality?.advisoryCount || 0}</td><td className="govuk-table__cell">Advisory data quality observations</td></tr>
                  </tbody>
                </table>
              </>
            ) : (
              <>
                <p className="govuk-body">Your data set has been uploaded as a draft.</p>
                <p className="govuk-body">A data quality report is being generated.</p>
                <div className="app-dqs-panel__loading__progress">
                  <span>Generating data quality report</span>
                  <div className="govuk-!-margin-left-2 app-!-text-muted">
                    <FontAwesomeIcon icon={faSpinner} pulse />
                  </div>
                </div>
                <p className="govuk-body">You can wait or close the browser. You can publish your data once the report is ready.</p>
              </>
            )}
            {dataQuality?.showUpdate || isFailure ? (
              <a role="button" className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0" href={updateUrl}>
                Update data
              </a>
            ) : null}
          </div>
        </div>
        {isSuccess ? (
          <form method="post" onSubmit={handlePublish} noValidate>
            <div className="govuk-form-group">
              <div className="govuk-checkboxes govuk-checkboxes--small" data-module="govuk-checkboxes">
                <div className="govuk-checkboxes__item">
                  <input
                    className="govuk-checkboxes__input"
                    id="id_consent"
                    name="consent"
                    type="checkbox"
                    checked={hasReviewed}
                    onChange={(event) => setHasReviewed(event.target.checked)}
                  />
                  <label className="govuk-label govuk-checkboxes__label" htmlFor="id_consent">
                    {DATA_QUALITY_CONSENT_LABEL}
                  </label>
                </div>
              </div>
            </div>
            <button
              type="submit"
              name="submit"
              value="submit"
              className="govuk-button"
              disabled={!hasReviewed || isPublishing}
            >
              {isPublishing ? 'Publishing...' : 'Publish data'}
            </button>
          </form>
        ) : null}
      </section>
    );
  };

  // Django `publish/revision_review/property_table.html`.
  const renderPropertyTable = () => (
    <table className="govuk-table dataset-property-table">
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Name</th>
          <td className="govuk-table__cell dont-break-out">{name}</td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Description</th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              {statusData?.description || ''}
              <span><a className="right-justify govuk-link" href={revisionEditUrl}>Edit</a></span>
            </div>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Short description</th>
          <td className="govuk-table__cell dont-break-out">
            <div className="flex-between">
              {statusData?.shortDescription || ''}
              <a className="govuk-link" href={revisionEditUrl}>Edit</a>
            </div>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Status</th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              <span className="status-indicator status-indicator--draft">Draft</span>
            </div>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Data quality report</th>
          <td className="govuk-table__cell">
            {reportId && criticalIssuesTag ? <p className="govuk-body govuk-!-margin-bottom-2">{criticalIssuesTag}</p> : null}
            <span className="no-wrap right-justify" id="id-publish-review-quality-report">
              {dataQuality?.status === 'SUCCESS' ? (
                <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={reportUrl}>View data quality report</a>
              ) : (
                'Generating...'
              )}
            </span>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Owner</th>
          <td className="govuk-table__cell">{ownerName}</td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">TransXChange version</th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              <span>{statusData?.transxchangeVersion || ''}</span>
              <span className="no-wrap right-justify">
                <a className="govuk-link" href={statusData?.downloadUrl}>Download .xml (TxC)</a>
              </span>
            </div>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">URL link</th>
          <td className="govuk-table__cell">
            <span className="no-wrap" id="id-publish-review-url-link">
              <a className="govuk-link" href={statusData?.publisherUrl || undefined}>Publisher URL</a>
            </span>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">Last updated</th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              <span>{formatDateTime(statusData?.lastModified)} by {statusData?.lastModifiedUser || 'System'}</span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );

  // Django `publish/revision_review/review_service_codes.html`.
  const renderServiceCodes = () => (
    <div>
      <h2 className="govuk-heading-l">Review Service Numbers</h2>
      <div className="govuk-accordion" data-module="govuk-accordion" id="accordion-default">
        {Object.entries(statusData?.distinctAttributes ?? {}).map(([licence, nocs], licenceIndex) => (
          <div className="govuk-accordion__section" key={licence}>
            <div className="govuk-accordion__section-header">
              <h2 className="govuk-accordion__section-heading">
                <span className="govuk-accordion__section-button" id={`accordion-default-heading-${licenceIndex + 1}`}>
                  {licence}
                </span>
              </h2>
            </div>
            {Object.entries(nocs).map(([noc, lines], nocIndex) => (
              <div
                key={noc}
                id={`sub-accordion-content-${licenceIndex + 1}`}
                className="govuk-accordion__section-content"
                aria-labelledby={`sub-accordion-heading-${licenceIndex + 1}`}
              >
                <div className="govuk-accordion__section govuk-!-padding-left-7">
                  <div className="govuk-accordion__section-header">
                    <h2 className="govuk-accordion__section-heading">
                      <span className="govuk-accordion__section-button" id={`sub-accordion-heading-${nocIndex + 1}`}>{noc}</span>
                    </h2>
                  </div>
                  <div
                    id={`sub-accordion-content-${nocIndex + 1}`}
                    className="govuk-accordion__section-content"
                    aria-labelledby={`sub-accordion-heading-${nocIndex + 1}`}
                  >
                    {Object.entries(lines).map(([line, serviceCodes]) =>
                      serviceCodes.map((serviceCode) => {
                        const query = new URLSearchParams({
                          line,
                          revision_id: String(statusData?.revisionId ?? ''),
                          service: serviceCode,
                        });
                        return (
                          <p className="govuk-body govuk-!-margin-left-7 govuk-!-padding-bottom-3 border-bottom-custom" key={`${line}-${serviceCode}`}>
                            <a className="govuk-link" href={`${publishAppPath(`${datasetPath}/review/detail/`)}?${query}`}>
                              {line} - {serviceCode}
                            </a>
                          </p>
                        );
                      }),
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );

  // Django `publish/revision_review/success_content.html`.
  const renderSuccessContent = () => (
    <>
      {renderValidationPanel()}
      {renderDataQualityPanel()}
      <div id="preview-section">
        <h2 className="govuk-heading-l dont-break-out">{name}</h2>
        {statusData?.revisionId ? <MapboxRouteMap revisionId={statusData.revisionId} ariaLabel="Interactive map showing timetable routes" /> : null}
        {renderPropertyTable()}
        {renderServiceCodes()}
        <div className="btn-group-justified">
          <a role="button" className="govuk-button govuk-button--secondary" href={deleteUrl}>Delete data</a>
        </div>
      </div>
    </>
  );

  // Django `publish/revision_review/no_file_to_process.html`.
  const renderNoValidFileState = () => (
    <>
      <PtiPanel>
        <h2 className="govuk-heading-m">Validation check - Failed</h2>
        <p className="govuk-body">The validation report checks for compliance against the mandated TxC 2.4 v1.1 profile.</p>
        <p className="govuk-body">
          <a className="govuk-link" href={statusData?.validationReportUrl}>Download validation report</a>
        </p>
        <p className="govuk-body">
          The timetables data supplied is non-compliant and cannot be submitted to BODS as per the{' '}
          <a href={`${guidanceUrl}?section=dataquality`} className="govuk-link">guidance</a>{' '}
          To pass the validation please address all outstanding issues in the validation report.
        </p>
      </PtiPanel>
      <a role="button" className="govuk-button govuk-!-margin-top-3" href={updateUrl}>Update data</a>
      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
      <h2 className="govuk-heading-l govuk-!-padding-top-5">{name}</h2>
      <ErrorSummaryTable name={name} ownerName={ownerName} />
      <DeleteComponent deleteUrl={deleteUrl} />
    </>
  );

  // Django `publish/revision_review/error_panel.html`.
  const renderErrorState = () => (
    <>
      <h2 className="govuk-heading-l govuk-!-padding-top-5">{name}</h2>
      <ErrorSummary
        errors={[statusData?.errorDescription || 'Something went wrong and we could not process your data set. Please try again later.']}
        title="Supplied data set has failed to upload"
        summaryId="timetable-upload-error-title"
        className="govuk-!-margin-bottom-0"
        titleClassName="govuk-!-margin-bottom-2"
        itemClassName="app-error-summary__item"
        tabIndex={-1}
      />
      <div className="govuk-!-padding-bottom-7 govuk-!-padding-top-5">
        <a role="button" className="govuk-button govuk-!-margin-bottom-0" href={updateUrl}>Publish correct data set</a>
      </div>
      <ErrorSummaryTable name={name} ownerName={ownerName} />
      <DeleteComponent deleteUrl={deleteUrl} />
    </>
  );

  if (isInitialLoading) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <p className="govuk-body">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <PublishStepper
          steps={[
            { label: stepperLabels[0], state: 'previous' },
            { label: stepperLabels[1], state: loading ? 'selected' : 'previous' },
            { label: stepperLabels[2], state: loading ? 'next' : 'selected' },
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
            {loading ? (
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
              renderErrorState()
            ) : (
              renderSuccessContent()
            )}
          </div>

          <TimetableHelpAside />
        </div>
      </div>
    </div>
  );
}
