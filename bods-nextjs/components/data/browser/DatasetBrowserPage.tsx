'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api-client';
import { HOSTS } from '@/lib/config';
import { useFilterOptions } from '@/hooks/useFilterOptions';
import { BrowseSearchBanner } from './BrowseSearchBanner';
import { DataBrowserResultCard } from './DataBrowserResultCard';

interface BrowserDatasetItem {
  id: number;
  name: string;
  description?: string;
  status?: string;
  modified?: string;
  operatorName?: string;
  organisation_name?: string;
  firstStartDate?: string | null;
  first_service_start?: string | null;
  avl_feed_last_checked?: string | null;
  adminAreas?: Array<{ name: string }>;
}

interface DatasetBrowserPageProps {
  title: string;
  breadcrumbLabel: string;
  description: string;
  placeholder: string;
  endpointPath: string;
  typeLabel: string;
  idLabel: string;
  lastUpdatedLabel: string;
  includeAreaFilter?: boolean;
  includeDateFilters?: boolean;
  includeStartDateInResult?: boolean;
}

interface ApiPaginated<T> {
  results: T[];
}

function formatDate(dateValue?: string | null): string {
  if (!dateValue) return '-';
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatCompactDateTime(dateValue?: string | null): string {
  if (!dateValue) return '';
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return '';
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const mi = String(date.getMinutes()).padStart(2, '0');
  const ss = String(date.getSeconds()).padStart(2, '0');
  return `${yyyy}${mm}${dd} ${hh}:${mi}:${ss}`;
}

export function DatasetBrowserPage({
  title,
  breadcrumbLabel,
  description,
  placeholder,
  endpointPath,
  typeLabel,
  idLabel,
  lastUpdatedLabel,
  includeAreaFilter = false,
  includeDateFilters = false,
  includeStartDateInResult = false,
}: DatasetBrowserPageProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { areas, organisations } = useFilterOptions();

  const [rawDatasets, setRawDatasets] = useState<BrowserDatasetItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const urlState = useMemo(
    () => ({
      q: searchParams.get('q') || '',
      area: searchParams.get('area') || '',
      organisation: searchParams.get('organisation') || '',
      status: searchParams.get('status') || 'published',
      start: searchParams.get('start') || '',
      publishedAt: searchParams.get('published_at') || '',
      ordering: searchParams.get('ordering') || '-modified',
    }),
    [searchParams]
  );

  const [q, setQ] = useState(urlState.q);
  const [area, setArea] = useState(urlState.area);
  const [organisation, setOrganisation] = useState(urlState.organisation);
  const [status, setStatus] = useState(urlState.status);
  const [start, setStart] = useState(urlState.start);
  const [publishedAt, setPublishedAt] = useState(urlState.publishedAt);

  useEffect(() => {
    setQ(urlState.q);
    setArea(urlState.area);
    setOrganisation(urlState.organisation);
    setStatus(urlState.status);
    setStart(urlState.start);
    setPublishedAt(urlState.publishedAt);
  }, [urlState]);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError('');
        const data = await api.get<ApiPaginated<BrowserDatasetItem>>(`${endpointPath}?limit=500`, {
          requireAuth: false,
        });
        setRawDatasets(Array.isArray(data.results) ? data.results : []);
      } catch {
        setError('Failed to load datasets');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [endpointPath]);

  const selectedOrgLabel = organisations.find((org) => org.value === urlState.organisation)?.label || '';
  const selectedAreaLabel = areas.find((item) => item.value === urlState.area)?.label || '';

  const datasets = useMemo(() => {
    return rawDatasets
      .filter((item) => {
        const query = urlState.q.trim().toLowerCase();
        if (!query) return true;
        return (
          (item.name || '').toLowerCase().includes(query) ||
          (item.description || '').toLowerCase().includes(query) ||
          (item.operatorName || item.organisation_name || '').toLowerCase().includes(query)
        );
      })
      .filter((item) => {
        if (!urlState.status) return true;
        const itemStatus = item.status || '';
        if (urlState.status === 'published') return itemStatus === 'live' || itemStatus === 'published';
        return itemStatus === urlState.status;
      })
      .filter((item) => {
        if (!urlState.organisation || !selectedOrgLabel) return true;
        const publisher = item.operatorName || item.organisation_name || '';
        return publisher.toLowerCase() === selectedOrgLabel.toLowerCase();
      })
      .filter((item) => {
        if (!includeAreaFilter || !urlState.area || !selectedAreaLabel) return true;
        const areaNames = (item.adminAreas || []).map((a) => a.name.toLowerCase());
        return areaNames.includes(selectedAreaLabel.toLowerCase());
      })
      .filter((item) => {
        if (!includeDateFilters || !urlState.start) return true;
        const startDate = new Date(item.firstStartDate || item.first_service_start || '').getTime();
        const threshold = new Date(urlState.start).getTime();
        return Number.isNaN(startDate) || Number.isNaN(threshold) || startDate >= threshold;
      })
      .filter((item) => {
        if (!includeDateFilters || !urlState.publishedAt) return true;
        const modified = new Date(item.modified || '').getTime();
        const threshold = new Date(urlState.publishedAt).getTime();
        return Number.isNaN(modified) || Number.isNaN(threshold) || modified >= threshold;
      })
      .sort((a, b) => {
        if (urlState.ordering === 'name') return (a.name || '').localeCompare(b.name || '');
        if (urlState.ordering === '-name') return (b.name || '').localeCompare(a.name || '');
        const aDate = new Date((a.avl_feed_last_checked || a.modified || '') as string).getTime();
        const bDate = new Date((b.avl_feed_last_checked || b.modified || '') as string).getTime();
        return bDate - aDate;
      });
  }, [
    includeAreaFilter,
    includeDateFilters,
    rawDatasets,
    selectedAreaLabel,
    selectedOrgLabel,
    urlState.area,
    urlState.organisation,
    urlState.ordering,
    urlState.publishedAt,
    urlState.q,
    urlState.start,
    urlState.status,
  ]);

  const updateQuery = (next: Partial<typeof urlState>) => {
    const params = new URLSearchParams(searchParams.toString());
    const merged = { ...urlState, ...next };
    const setOrDelete = (key: string, value: string) => (value ? params.set(key, value) : params.delete(key));
    setOrDelete('q', merged.q);
    setOrDelete('area', merged.area);
    setOrDelete('organisation', merged.organisation);
    setOrDelete('status', merged.status);
    setOrDelete('start', merged.start);
    setOrDelete('published_at', merged.publishedAt);
    setOrDelete('ordering', merged.ordering);
    router.push(params.toString() ? `${pathname}?${params.toString()}` : pathname);
  };

  return (
    <>
      <div className="govuk-width-container">
        <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item"><a className="govuk-breadcrumbs__link" href={HOSTS.root}>Bus Open Data Service</a></li>
            <li className="govuk-breadcrumbs__list-item"><Link className="govuk-breadcrumbs__link" href="/">Find Bus Open Data</Link></li>
            <li className="govuk-breadcrumbs__list-item"><Link className="govuk-breadcrumbs__link" href="/data">Browse</Link></li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">{breadcrumbLabel}</li>
          </ol>
        </nav>
      </div>

      <BrowseSearchBanner
        title={title}
        description={description}
        placeholder={placeholder}
        searchValue={q}
        onSearchChange={setQ}
        onSearchSubmit={() => updateQuery({ q })}
      />

      <div className="govuk-width-container">
        <main className="govuk-main-wrapper" id="main-content" role="main">
          <div className="govuk-grid-row govuk-!-margin-top-8">
            <div className="govuk-grid-column-one-third">
              <h2 className="govuk-heading-m">Filter by</h2>
              {includeAreaFilter && (
                <div className="govuk-form-group">
                  <label className="govuk-label" htmlFor="area">Geographical area</label>
                  <select id="area" className="govuk-select govuk-!-width-full" value={area} onChange={(e) => setArea(e.target.value)}>
                    <option value="">All geographical areas</option>
                    {areas.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                </div>
              )}
              <div className="govuk-form-group">
                <label className="govuk-label" htmlFor="organisation">Publisher</label>
                <select id="organisation" className="govuk-select govuk-!-width-full" value={organisation} onChange={(e) => setOrganisation(e.target.value)}>
                  <option value="">All publishers</option>
                  {organisations.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </div>
              <div className="govuk-form-group">
                <label className="govuk-label" htmlFor="status">Status</label>
                <select id="status" className="govuk-select govuk-!-width-full" value={status} onChange={(e) => setStatus(e.target.value)}>
                  <option value="">All statuses</option>
                  <option value="published">Published</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              {includeDateFilters && (
                <>
                  <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="start">Timetable start date after</label>
                    <div className="govuk-hint">For example: 21/11/2014</div>
                    <input id="start" type="date" className="govuk-input govuk-!-width-full" value={start} onChange={(e) => setStart(e.target.value)} />
                  </div>
                  <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="published_at">Timetable last updated after</label>
                    <div className="govuk-hint">For example: 21/11/2014</div>
                    <input id="published_at" type="date" className="govuk-input govuk-!-width-full" value={publishedAt} onChange={(e) => setPublishedAt(e.target.value)} />
                  </div>
                </>
              )}
              <button className="govuk-button" type="button" onClick={() => updateQuery({ area, organisation, status, start, publishedAt })}>Apply filter</button>
            </div>

            <div className="govuk-grid-column-two-thirds">
              <div className="app-data-browser__results-heading"><span className="govuk-body">{datasets.length.toLocaleString()} results</span></div>
              {status && (
                <div className="app-data-browser__filter-pillbox">
                  <span className="app-data-browser__filter-pill">
                    <button type="button" className="app-data-browser__pill-remove" onClick={() => updateQuery({ status: '' })}>×</button>
                    {status === 'published' ? 'Published' : 'Inactive'}
                  </span>
                </div>
              )}
              <div className="app-data-browser__sort-control">
                <label className="govuk-label" htmlFor="ordering">Sort by</label>
                <select className="govuk-select" id="ordering" value={urlState.ordering} onChange={(e) => updateQuery({ ordering: e.target.value })}>
                  <option value="-modified">Recently updated</option>
                  <option value="name">Data set name A-Z</option>
                  <option value="-name">Data set name Z-A</option>
                </select>
              </div>
              {error && <p className="govuk-body">{error}</p>}
              {isLoading ? (
                <p className="govuk-body">Loading results...</p>
              ) : (
                datasets.map((dataset, index) => {
                  const statusValue = dataset.status || 'published';
                  const lastUpdatedValue = dataset.avl_feed_last_checked || dataset.modified;
                  const stamp = formatCompactDateTime(lastUpdatedValue);
                  const titleValue = `${dataset.name} ${dataset.id}${stamp ? `  ${stamp}` : ''}`;
                  const keyValues = [
                    { key: 'Data type:', value: typeLabel },
                    { key: idLabel, value: String(dataset.id) },
                    { key: 'Publisher:', value: dataset.operatorName || dataset.organisation_name || '-' },
                  ];
                  if (includeStartDateInResult) {
                    keyValues.push({ key: 'Timetable start date:', value: formatDate(dataset.firstStartDate || dataset.first_service_start) });
                  }
                  keyValues.push({ key: lastUpdatedLabel, value: formatDate(lastUpdatedValue) });
                  return (
                    <div className="app-data-browser__result-item" key={dataset.id}>
                      {index > 0 && <hr className="app-data-browser__result-divider" />}
                      <DataBrowserResultCard
                        title={titleValue}
                        href={`/data/${dataset.id}`}
                        status={statusValue}
                        statusLabel={statusValue === 'inactive' ? 'Inactive' : 'Published'}
                        keyValues={keyValues}
                        description={dataset.description}
                      />
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

