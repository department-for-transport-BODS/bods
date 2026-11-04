'use client';

import Link from 'next/link';
import { useParams, usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useState, type FormEvent } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCaretDown, faCaretUp } from '@fortawesome/free-solid-svg-icons';
import { api } from '@/lib/api-client';
import { useApiResource } from '@/hooks/useApiResource';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import { Pagination } from '@/components/shared/Pagination';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { publishAppPath } from '@/config/client';
import {
  SEASONAL_SERVICE_HEADING,
  SeasonalServiceBreadcrumbs,
  addNewPath,
  pageQuery,
  reviewTimetablesPath,
  seasonalServicesApiPath,
  type SeasonalServiceOrganisation,
  type SeasonalServiceRow,
} from './shared';

interface SeasonalServiceListResponse extends SeasonalServiceOrganisation {
  counter: number;
  results: SeasonalServiceRow[];
  sort: string;
  pagination: {
    page: number;
    totalPages: number;
    count: number;
    pageSize: number;
  };
}

const COLUMNS = [
  { key: 'licence_number', label: 'Licence number' },
  { key: 'service_code', label: 'Service code' },
  { key: 'service_begins', label: 'Service begins' },
  { key: 'service_ends', label: 'Service ends' },
];

function sortState(columnKey: string, sort: string): 'asc' | 'desc' | 'none' {
  if (sort === columnKey) return 'asc';
  if (sort === `-${columnKey}`) return 'desc';
  return 'none';
}

export function SeasonalServicesListContent() {
  const params = useParams();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const sortParam = searchParams.get('sort') || '';
  const pageParam = searchParams.get('page') || '';
  const [reloadKey, setReloadKey] = useState(0);
  const { isSubmitting, submitError, handleSubmit } = useFormSubmit();

  const loadList = useCallback(async () => {
    const query = new URLSearchParams();
    if (sortParam) query.set('sort', sortParam);
    if (pageParam) query.set('page', pageParam);
    const queryString = query.toString();
    return api.get<SeasonalServiceListResponse>(
      `${seasonalServicesApiPath(orgId)}${queryString ? `?${queryString}` : ''}`,
    );
    // reloadKey changes after a delete so the list is fetched again even when the URL is unchanged.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, sortParam, pageParam, reloadKey]);

  const { data, isLoading, error } = useApiResource<SeasonalServiceListResponse>(
    loadList,
    'Unable to load seasonal services.',
  );

  if (isLoading && !data) {
    return <LoadingSpinner message="Loading seasonal services" />;
  }

  if (error && !data) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <ErrorDisplay message={error} />
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const currentPage = data.pagination.page;
  const handleDelete = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const id = Number(submitter?.value);
    if (!id) return;

    void handleSubmit(async () => {
      const response = await api.post<{ deleted: boolean; page: number }>(
        seasonalServicesApiPath(orgId, 'delete/'),
        { id, page: String(currentPage) },
      );
      const query = new URLSearchParams(searchParams.toString());
      query.set('page', String(response.page));
      router.replace(`${pathname}?${query.toString()}`);
      setReloadKey((key) => key + 1);
    });
  };

  return (
    <>
      <SeasonalServiceBreadcrumbs orgId={orgId} organisation={data} />

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row">
            <div className="govuk-!-margin-top-5">
              <h1 className="govuk-heading-xl app-masthead__title">{SEASONAL_SERVICE_HEADING}</h1>
              <p className="govuk-body">
                BODS marks your service as requiring attention if it has been registered with the OTC and you have not
                published any timetable data to BODS. From within this page, you can manage your seasonal services by
                providing an operating start and end date to let BODS know when to expect your data for a service.
              </p>
              <p className="govuk-body">
                BODS will not alert you for not publishing data for a service until 42 days prior to the service start
                date listed below
              </p>
              <div className="review-banner">
                <div className="review-stat govuk-!-margin-bottom-0">
                  <div>
                    <span className="review-stat__top">{data.counter}</span>
                  </div>
                  <p className="review-stat__description">Seasonal services</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container seasonal-services-page">
        <div className="govuk-main-wrapper app-main-class">
          <div className="govuk-width-container">
            <div className="govuk-grid-row govuk-!-margin-top-0">
              <div className="govuk-width-container">
                <div className="govuk-grid-column-full custom_govuk_table_border">
                  <form method="post" onSubmit={handleDelete}>
                    <div>
                      <table className="custom_govuk_table ">
                        <thead className="govuk-table__head ">
                          <tr className="govuk-table__row">
                            {COLUMNS.map((column) => {
                              const state = sortState(column.key, data.sort);
                              const nextSort = state === 'asc' ? `-${column.key}` : column.key;
                              const ariaSort = { asc: 'ascending', desc: 'descending', none: 'none' }[state] as
                                | 'ascending'
                                | 'descending'
                                | 'none';
                              return (
                                <th
                                  key={column.key}
                                  aria-sort={ariaSort}
                                  role="columnheader"
                                  scope="col"
                                  className={`${state === 'none' ? '' : `${state} `}govuk-table__header orderable`}
                                >
                                  <Link className="column-header-link" role="button" href={`?sort=${nextSort}&page=1`}>
                                    {column.label}
                                    <span className="hide-using-position">Sort your data by {column.label}</span>
                                  </Link>
                                  <FontAwesomeIcon className="order-up" icon={faCaretUp} />
                                  <FontAwesomeIcon className="order-down" icon={faCaretDown} />
                                </th>
                              );
                            })}
                            <th
                              aria-sort="none"
                              role="columnheader"
                              scope="col"
                              className="actions-column-table govuk-table__header"
                            >
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="govuk-table__body ">
                          {data.results.length === 0 ? (
                            <tr className="govuk-table__row">
                              <td className="govuk-table__cell" colSpan={5}>
                                <div className="seasonal_service_empty_body_table">
                                  <p>No seasonal services added.</p>
                                  <br />
                                  <p>Click &apos;Add new date range&apos; to add a service.</p>
                                </div>
                              </td>
                            </tr>
                          ) : (
                            data.results.map((row) => (
                              <tr key={row.id} className="govuk-table__row">
                                <td className="govuk-table__cell">{row.licenceNumber}</td>
                                <td className="govuk-table__cell">{row.serviceCode}</td>
                                <td className="govuk-table__cell">{row.serviceBegins}</td>
                                <td className="govuk-table__cell">{row.serviceEnds}</td>
                                <td className="govuk-table__cell">
                                  <Link
                                    className="govuk-link"
                                    href={`${publishAppPath(
                                      `/org/${orgId}/dataset/timetable/seasonal-service/${row.id}/edit-date`,
                                    )}?page=${currentPage}&`}
                                  >
                                    Edit dates
                                  </Link>
                                  <button
                                    type="submit"
                                    name="id"
                                    value={row.id}
                                    className="button-table-link govuk-!-margin-left-1"
                                    disabled={isSubmitting}
                                  >
                                    Delete
                                  </button>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                      <Pagination
                        currentPage={currentPage}
                        totalPages={data.pagination.totalPages}
                        showSinglePage
                      />
                    </div>
                  </form>
                  {submitError && <p className="govuk-error-message">{submitError}</p>}
                </div>
              </div>
            </div>
          </div>
          <div className="govuk-width-container">
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <Link
                  role="button"
                  className="govuk-button govuk-button--secondary govuk-!-margin-top-5"
                  href={`${addNewPath(orgId)}${pageQuery(String(currentPage))}`}
                >
                  Add new date range
                </Link>
                <Link
                  role="button"
                  className="govuk-button govuk-button--secondary govuk-!-margin-top-5"
                  href={reviewTimetablesPath(orgId)}
                >
                  Close
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
