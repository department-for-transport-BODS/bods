'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';
import { useTabs } from '@/hooks/useTabs';

type DataQualityObservation = {
  observation: string;
  slug: string | null;
  count: number;
  suppressedCount: number;
};

type DataQualityCategory = {
  category: string;
  count: number;
  suppressedCount: number;
  observations: DataQualityObservation[];
};

type DataQualityLevel = {
  level: string;
  count: number;
  intro: string;
  categories: DataQualityCategory[];
};

type DataQualityReportResponse = {
  reportId: number;
  title: string;
  busServicesAffected: number;
  hasCriticalIssues: boolean;
  levels: DataQualityLevel[];
};

const STAT_LEVELS = ['Critical', 'Advisory', 'Feedback'];
const LEVELS_WITH_SUPPRESSED = new Set(['Advisory', 'Feedback']);

const pluralise = (count: number) => (count === 1 ? '' : 's');

export default function TimetableDataQualityReportPage() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [report, setReport] = useState<DataQualityReportResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { selectedTab, getTabProps, getPanelProps } = useTabs(report?.levels.map(({ level }) => level) ?? []);

  useEffect(() => {
    let cancelled = false;
    api
      .get<DataQualityReportResponse>(`/api/publish/timetables/data-quality-report/${orgId}/${datasetId}/`)
      .then((data) => {
        if (cancelled) return;
        document.title = 'Data quality report';
        setReport(data);
      })
      .catch(() => {
        if (!cancelled) setErrorMessage('Unable to load the data quality report. Please refresh and try again.');
      });
    return () => {
      cancelled = true;
    };
  }, [orgId, datasetId]);

  const renderReport = (data: DataQualityReportResponse) => {
    const csvUrl = `/api/publish/timetables/data-quality-report/${orgId}/${datasetId}/${data.reportId}/csv/`;
    const levelStats = STAT_LEVELS.flatMap((levelName) => {
      const level = data.levels.find((item) => item.level === levelName);
      return level ? [{ key: levelName, count: level.count, label: <>{levelName} observation{pluralise(level.count)}</>, labelClassName: 'govuk-!-padding-1' }] : [];
    });
    const stats = [
      {
        key: 'services',
        count: data.busServicesAffected,
        label: <>Bus service{pluralise(data.busServicesAffected)}<br />affected</>,
        labelClassName: '',
      },
      ...levelStats,
    ];

    return (
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <div className="govuk-!-margin-bottom-4 flex-container">
            <h1 className="govuk-!-font-size-48 govuk-list govuk-!-margin-0">
              <span className="govuk-!-font-weight-bold">Data quality report</span>
            </h1>
            <div className="content-center">
              <span
                className={`govuk-tag ${data.hasCriticalIssues ? 'govuk-tag--red' : 'govuk-tag--green'} govuk-!-margin-left-3 govuk-!-font-size-16 govuk-!-text-align-centre`}
              >
                {data.hasCriticalIssues ? 'CRITICAL ISSUES' : 'NO CRITICAL ISSUES'}
              </span>
            </div>
          </div>
          <h2 className="govuk-list govuk-!-font-size-24">{data.title}</h2>
          <ul className="govuk-list">
            <li>Please find your data quality observations below.</li>
            <li>
              <Link
                className="govuk-link"
                href={publishAppPath('/guidance/data-quality-definitions')}
                target="_blank"
              >
                What are the different type of observations?
              </Link>
            </li>
            <li>
              <a className="govuk-link" href={csvUrl} download>
                Download data quality report.csv
              </a>
            </li>
          </ul>
          <div className="govuk-grid-row govuk-!-margin-bottom-4">
            <div className="govuk-grid-column-full govuk-grid-column-three-quarters-from-desktop">
              <div className="govuk-grid-row">
                {stats.map((stat) => (
                  <div className="govuk-grid-column-one-quarter-from-desktop" key={stat.key}>
                    <p className="govuk-heading-xl govuk-!-margin-bottom-0">{stat.count}</p>
                    <p className={`govuk-body-s govuk-!-font-weight-bold ${stat.labelClassName}`.trim()}>{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {data.levels.length ? (
            <div className="govuk-tabs">
              <h2 className="govuk-tabs__title">Contents</h2>
              <ul className="govuk-tabs__list" role="tablist">
                {data.levels.map(({ level }) => (
                  <li
                    key={level}
                    className={`govuk-tabs__list-item${selectedTab === level ? ' govuk-tabs__list-item--selected' : ''}`}
                    role="presentation"
                  >
                    <a
                      className="govuk-tabs__tab"
                      {...getTabProps(level)}
                    >
                      {level}
                    </a>
                  </li>
                ))}
              </ul>
              {data.levels.map((level) => {
                const showSuppressed = LEVELS_WITH_SUPPRESSED.has(level.level);
                return (
                  <div
                    key={level.level}
                    className="govuk-tabs__panel"
                      {...getPanelProps(level.level)}
                  >
                    <h2 className="govuk-heading-l">
                      {level.level} observations ({level.count})
                    </h2>
                    <p className="govuk-body">{level.intro}</p>
                    {level.categories.map((category) => (
                      <table className="govuk-table" key={category.category}>
                        <caption className="govuk-table__caption govuk-table__caption--s govuk-!-font-weight-bold govuk-!-font-size-24">
                          {category.category} ({category.count})
                        </caption>
                        <thead className="govuk-table__head">
                          <tr className="govuk-table__row">
                            <th
                              scope="col"
                              className={`govuk-table__header ${showSuppressed ? 'govuk-!-width-one-quarter' : 'govuk-!-width-one-half'}`}
                            >
                              Number of observation{pluralise(category.count)}
                            </th>
                            {showSuppressed ? (
                              <th scope="col" className="govuk-table__header govuk-!-width-one-third">
                                Number of suppressed observation{pluralise(category.suppressedCount)}
                              </th>
                            ) : null}
                            <th scope="col" className="govuk-table__header">Observation category</th>
                          </tr>
                        </thead>
                        <tbody className="govuk-table__body">
                          {category.observations.map((observation) => (
                            <tr className="govuk-table__row" key={observation.observation}>
                              <th scope="row" className="govuk-table__header govuk-!-font-weight-regular">
                                {observation.count}
                              </th>
                              {showSuppressed ? (
                                <td className="govuk-table__cell">{observation.suppressedCount}</td>
                              ) : null}
                              <td className="govuk-table__cell">
                                {observation.slug ? (
                                  <Link
                                    href={`/publish/org/${orgId}/dataset/timetable/${datasetId}/report/${data.reportId}/${observation.slug}`}
                                  >
                                    {observation.observation}
                                  </Link>
                                ) : (
                                  observation.observation
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ))}
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>
      </div>
    );
  };

  return (
    <ProtectedRoute>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          {errorMessage ? <ErrorSummary errors={[errorMessage]} /> : null}
          {!report && !errorMessage ? <p className="govuk-body">Loading...</p> : null}
          {report ? renderReport(report) : null}
        </div>
      </div>
    </ProtectedRoute>
  );
}
