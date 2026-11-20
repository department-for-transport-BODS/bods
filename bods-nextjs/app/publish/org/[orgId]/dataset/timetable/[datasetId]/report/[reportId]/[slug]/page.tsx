'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ExtraInfoTable, type ObservationDefinition } from '@/components/publish/data-quality/ExtraInfoTable';
import { ErrorSummary, Pagination } from '@/components/shared';
import { dataPath } from '@/config/client';
import { api } from '@/lib/api-client';
import { SuppressAllButton, SuppressCheckbox, observationApiPath, suppressObservations } from './SuppressControls';

type ObservationRow = {
  serviceCode: string;
  lineName: string;
  details: string;
  isSuppressed: boolean;
};

type ObservationListResponse = {
  reportId: number;
  revisionId: number;
  isPublished: boolean;
  observation: ObservationDefinition;
  hasDetail: boolean;
  canSuppress: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  rows: ObservationRow[];
};

const SUPPRESS_ERROR = 'Unable to update the observation. Please try again.';

function serviceUrl(data: ObservationListResponse, orgId: string, datasetId: string, row: ObservationRow) {
  const line = encodeURIComponent(row.lineName);
  const service = encodeURIComponent(row.serviceCode);
  if (data.isPublished) {
    return dataPath(`/timetable/dataset/${datasetId}/detail/?line=${line}&service=${service}`);
  }
  return `/publish/org/${orgId}/dataset/timetable/${datasetId}/review/detail?line=${line}&revision_id=${data.revisionId}&service=${service}`;
}

function ObservationList() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const reportId = params.reportId as string;
  const slug = params.slug as string;
  const page = searchParams.get('page') ?? '1';
  const apiPath = observationApiPath(orgId, datasetId, reportId, slug);
  const basePath = `/publish/org/${orgId}/dataset/timetable/${datasetId}/report/${reportId}/${slug}`;

  const [data, setData] = useState<ObservationListResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setErrorMessage(null);
    api
      .get<ObservationListResponse>(`${apiPath}?page=${encodeURIComponent(page)}`)
      .then((response) => {
        if (cancelled) return;
        setData(response);
        document.title = `${response.observation.title} observations list`;
      })
      .catch(() => {
        if (!cancelled) setErrorMessage('Unable to load the observations. Please refresh and try again.');
      });
    return () => {
      cancelled = true;
    };
  }, [apiPath, page]);

  const updateRows = useCallback((update: (row: ObservationRow) => ObservationRow) => {
    setData((current) => (current ? { ...current, rows: current.rows.map(update) } : current));
  }, []);

  const suppressRow = async (row: ObservationRow, isSuppressed: boolean) => {
    setSaving(true);
    setErrorMessage(null);
    try {
      await suppressObservations(apiPath, { serviceCode: row.serviceCode, lineName: row.lineName, isSuppressed });
      updateRows((item) =>
        item.serviceCode === row.serviceCode && item.lineName === row.lineName ? { ...item, isSuppressed } : item,
      );
    } catch {
      setErrorMessage(SUPPRESS_ERROR);
    } finally {
      setSaving(false);
    }
  };

  const suppressAll = async (isSuppressed: boolean) => {
    setSaving(true);
    setErrorMessage(null);
    try {
      await suppressObservations(apiPath, { isSuppressed });
      updateRows((item) => ({ ...item, isSuppressed }));
    } catch {
      setErrorMessage(SUPPRESS_ERROR);
    } finally {
      setSaving(false);
    }
  };

  const renderTable = (response: ObservationListResponse) => {
    const allSuppressed = response.rows.length > 0 && response.rows.every((row) => row.isSuppressed);
    const showSuppress = response.canSuppress && response.rows.length > 0;
    return (
      <>
        <table className="govuk-table custom_govuk_table custom_govuk_table--dqs">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header">Service ({response.rows.length})</th>
              <th scope="col" className="govuk-table__header">Details</th>
              {showSuppress ? (
                <th scope="col" className="govuk-table__header govuk-!-width-one-quarter">
                  <SuppressAllButton
                    allSuppressed={allSuppressed}
                    disabled={saving}
                    onClick={() => suppressAll(!allSuppressed)}
                  />
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {response.rows.map((row, index) => (
              <tr className="govuk-table__row" key={`${row.serviceCode}-${row.lineName}`}>
                <td className="govuk-table__cell govuk-!-padding-bottom-0">
                  <a href={serviceUrl(response, orgId, datasetId, row)}>
                    {row.lineName} - {row.serviceCode}
                  </a>
                </td>
                <td className="govuk-table__cell govuk-!-padding-bottom-0">
                  {response.hasDetail ? (
                    <Link
                      href={`${basePath}/detail?line=${encodeURIComponent(row.lineName)}&service=${encodeURIComponent(row.serviceCode)}`}
                    >
                      {row.details}
                    </Link>
                  ) : (
                    row.details
                  )}
                </td>
                {showSuppress ? (
                  <td className="govuk-table__cell govuk-!-padding-bottom-0">
                    <SuppressCheckbox
                      id={`checkbox-suppress-${index + 1}`}
                      checked={row.isSuppressed}
                      disabled={saving}
                      onChange={(checked) => suppressRow(row, checked)}
                    />
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination currentPage={response.page} totalPages={response.totalPages} showSinglePage />
      </>
    );
  };

  const observation = data?.observation;

  return (
    <div className="govuk-width-container">
      <div className="govuk-back-link-wrapper">
        <Link className="govuk-back-link" href={`/publish/org/${orgId}/dataset/timetable/${datasetId}/report/draft`}>
          Back
        </Link>
      </div>
      <div className="govuk-main-wrapper">
        {errorMessage ? <ErrorSummary errors={[errorMessage]} /> : null}
        {!data && !errorMessage ? <p className="govuk-body">Loading...</p> : null}
        {data && observation ? (
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <h1 className="govuk-heading-xl" id="observation-title">
                {observation.title}
              </h1>
              {observation.text ? (
                <p className="govuk-body-m" dangerouslySetInnerHTML={{ __html: observation.text }} />
              ) : null}
              {observation.impacts ? (
                <>
                  <h2 className="govuk-heading-m">Impacts</h2>
                  <p className="govuk-body-m" dangerouslySetInnerHTML={{ __html: observation.impacts }} />
                  {observation.extraInfo.length ? (
                    <details className="govuk-details">
                      <summary className="govuk-details__summary">
                        <span className="govuk-details__summary-text">What are the different types of bus stops?</span>
                      </summary>
                      <div className="govuk-details__text">
                        <ExtraInfoTable extraInfo={observation.extraInfo} />
                      </div>
                    </details>
                  ) : null}
                </>
              ) : null}
              {observation.resolve ? (
                <>
                  <h2 className="govuk-heading-m">How to resolve</h2>
                  <p className="govuk-body-m" dangerouslySetInnerHTML={{ __html: observation.resolve }} />
                </>
              ) : null}
              {observation.preamble ? <p className="govuk-body-m">{observation.preamble}</p> : null}
              {renderTable(data)}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function ObservationListPage() {
  return (
    <ProtectedRoute>
      <Suspense fallback={null}>
        <ObservationList />
      </Suspense>
    </ProtectedRoute>
  );
}
