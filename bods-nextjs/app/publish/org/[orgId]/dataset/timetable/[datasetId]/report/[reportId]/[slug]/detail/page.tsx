'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FeedbackTooltip } from '@/components/publish/data-quality/FeedbackTooltip';
import { ErrorSummary, Pagination } from '@/components/shared';
import { api } from '@/lib/api-client';
import { SuppressAllButton, SuppressCheckbox, observationApiPath, suppressObservations } from '../SuppressControls';

type DetailRow = {
  rowId: number | null;
  isSuppressed: boolean;
  feedback: string;
  values: Record<string, string>;
};

type ObservationDetailResponse = {
  reportId: number;
  title: string;
  subtitle: string;
  subtitleDescription: string;
  totalDescription: string;
  totalDescriptionShort: string;
  listText: string;
  isFeedback: boolean;
  canSuppress: boolean;
  columns: { key: string; label: string }[];
  page: number;
  totalPages: number;
  totalCount: number;
  rows: DetailRow[];
};

const SUPPRESS_ERROR = 'Unable to update the observation. Please try again.';

function ObservationDetail() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const reportId = params.reportId as string;
  const slug = params.slug as string;
  const line = searchParams.get('line') ?? '';
  const service = searchParams.get('service') ?? '';
  const page = searchParams.get('page') ?? '1';
  const apiPath = observationApiPath(orgId, datasetId, reportId, slug);
  const query = new URLSearchParams({ line, service, page }).toString();
  const requestUrl = `${apiPath}detail/?${query}`;

  const [loaded, setLoaded] = useState<{ requestUrl: string; data: ObservationDetailResponse } | null>(null);
  const data = loaded?.requestUrl === requestUrl ? loaded.data : null;
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [openTooltip, setOpenTooltip] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setErrorMessage(null);
    setOpenTooltip(null);
    api
      .get<ObservationDetailResponse>(requestUrl)
      .then((response) => {
        if (cancelled) return;
        setLoaded({ requestUrl, data: response });
        document.title = `${response.title} observation detail`;
      })
      .catch(() => {
        if (!cancelled) setErrorMessage('Unable to load the observation details. Please refresh and try again.');
      });
    return () => {
      cancelled = true;
    };
  }, [requestUrl]);

  const suppress = async (isSuppressed: boolean, row?: DetailRow) => {
    setSaving(true);
    setErrorMessage(null);
    try {
      await suppressObservations(apiPath, {
        serviceCode: service,
        lineName: line,
        rowId: row?.rowId ?? null,
        isSuppressed,
      });
      setLoaded((current) =>
        current?.requestUrl === requestUrl
          ? {
              ...current,
              data: {
                ...current.data,
                rows: current.data.rows.map((item) => (!row || item.rowId === row.rowId ? { ...item, isSuppressed } : item)),
              },
            }
          : current,
      );
    } catch {
      setErrorMessage(SUPPRESS_ERROR);
    } finally {
      setSaving(false);
    }
  };

  const renderCell = (response: ObservationDetailResponse, row: DetailRow, key: string, index: number) => {
    const value = row.values[key];
    if (response.isFeedback && key === 'message' && row.feedback) {
      return (
        <FeedbackTooltip
          id={`feedback-${index + 1}`}
          label={value || 'Read message here'}
          feedback={row.feedback}
          isOpen={openTooltip === index}
          onToggle={() => setOpenTooltip((current) => (current === index ? null : index))}
        />
      );
    }
    return value;
  };

  const renderTable = (response: ObservationDetailResponse) => {
    const showSuppress = response.canSuppress && response.rows.length > 0;
    const allSuppressed = response.rows.length > 0 && response.rows.every((row) => row.isSuppressed);
    return (
      <>
        <table className="govuk-table custom_govuk_table custom_govuk_table--dqs">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              {response.columns.map((column) => (
                <th scope="col" className="govuk-table__header" key={column.key}>
                  {column.label}
                </th>
              ))}
              {showSuppress ? (
                <th scope="col" className="govuk-table__header govuk-!-width-one-quarter">
                  <SuppressAllButton
                    allSuppressed={allSuppressed}
                    disabled={saving}
                    onClick={() => suppress(!allSuppressed)}
                  />
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {response.rows.map((row, index) => (
              <tr className="govuk-table__row" key={row.rowId || index}>
                {response.columns.map((column) => (
                  <td className="govuk-table__cell" key={column.key}>
                    {renderCell(response, row, column.key, index)}
                  </td>
                ))}
                {showSuppress ? (
                  <td className="govuk-table__cell govuk-!-padding-bottom-0">
                    <SuppressCheckbox
                      id={`checkbox-suppress-${index + 1}`}
                      checked={row.isSuppressed}
                      disabled={saving}
                      onChange={(checked) => suppress(checked, row)}
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

  return (
    <div className="govuk-width-container">
      <div className="govuk-back-link-wrapper">
        <Link
          className="govuk-back-link"
          href={`/publish/org/${orgId}/dataset/timetable/${datasetId}/report/${reportId}/${slug}`}
        >
          Back
        </Link>
      </div>
      <div className="govuk-main-wrapper">
        {errorMessage ? <ErrorSummary errors={[errorMessage]} /> : null}
        {!data && !errorMessage ? <p className="govuk-body">Loading...</p> : null}
        {data ? (
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <span id="observation-title" className="govuk-caption-xl govuk-!-margin-bottom-6">
                {data.title}
              </span>
              <h1 className="govuk-heading-xl">{data.subtitle}</h1>
              <h2 className="govuk-heading-xl govuk-!-margin-bottom-4">{data.subtitleDescription}</h2>
              <div className="total_vehicles">
                <span className="govuk-heading-xl govuk-!-margin-0">{data.totalCount}</span>
                <span className="govuk-body-s">
                  {data.totalDescription}
                  <br />
                  {data.totalDescriptionShort}
                </span>
              </div>
              <p className="govuk-body">
                Below is list of the {data.listText} that are affected by the “{data.title}” data quality
                observation. Please refer back to these journeys in your scheduling tool and update the
                corresponding timetable(s) to address this.
              </p>
              {renderTable(data)}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function ObservationDetailPage() {
  return (
    <ProtectedRoute>
      <Suspense fallback={null}>
        <ObservationDetail />
      </Suspense>
    </ProtectedRoute>
  );
}
