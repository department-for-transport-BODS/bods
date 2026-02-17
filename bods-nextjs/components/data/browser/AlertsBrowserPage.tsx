'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api-client';
import { HOSTS } from '@/lib/config';
import { BrowseSearchBanner } from './BrowseSearchBanner';
import { DataBrowserResultCard } from './DataBrowserResultCard';

interface AlertsBrowserPageProps {
  title: string;
  breadcrumbLabel: string;
  description: string;
  placeholder: string;
  endpointPath: string;
}

interface AlertItem {
  id: string;
  title: string;
  status: string;
  lastUpdated: string;
  description?: string;
  keyValues: Array<{ key: string; value: string }>;
}

function asRecord(value: unknown): Record<string, unknown> {
  return (value && typeof value === 'object' ? value : {}) as Record<string, unknown>;
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function formatDate(dateValue?: string): string {
  if (!dateValue) {
    return '-';
  }
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function toAlertItem(input: unknown, index: number): AlertItem {
  const record = asRecord(input);
  const stats = asRecord(record.stats);
  const id =
    asString(record.id) ||
    asString(record.disruptionId) ||
    asString(record.situationNumber) ||
    String(index + 1);

  const title =
    asString(record.name) ||
    asString(record.summary) ||
    asString(record.reason) ||
    asString(record.lineRef) ||
    `Record ${id}`;

  const lastUpdated =
    asString(stats.lastUpdated) ||
    asString(record.lastUpdated) ||
    asString(record.modified) ||
    asString(record.updatedAt);

  const status = asString(record.status) || (stats.totalDisruptionsCount ? 'published' : 'inactive');

  const keyValues: Array<{ key: string; value: string }> = [];
  const activeCount = stats.totalDisruptionsCount;
  if (typeof activeCount === 'number') {
    keyValues.push({ key: 'Active disruptions:', value: String(activeCount) });
  }
  keyValues.push({ key: 'Last updated:', value: formatDate(lastUpdated) });

  const operator = asString(record.operatorRef) || asString(record.organisation_name);
  if (operator) {
    keyValues.push({ key: 'Operator:', value: operator });
  }

  return {
    id,
    title,
    status,
    lastUpdated,
    description: asString(record.description),
    keyValues,
  };
}

export function AlertsBrowserPage({
  title,
  breadcrumbLabel,
  description,
  placeholder,
  endpointPath,
}: AlertsBrowserPageProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [rawItems, setRawItems] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const q = searchParams.get('q') || '';
  const ordering = searchParams.get('ordering') || '-modified';
  const [searchValue, setSearchValue] = useState(q);

  useEffect(() => {
    setSearchValue(q);
  }, [q]);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError('');
        const data = await api.get<unknown>(`${endpointPath}?limit=500`, { requireAuth: false });
        const record = asRecord(data);
        const list = Array.isArray(record.results)
          ? record.results
          : Array.isArray(data)
            ? data
            : [];
        setRawItems(list.map((item, index) => toAlertItem(item, index)));
      } catch {
        setError('Failed to load results');
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [endpointPath]);

  const filteredAndSorted = useMemo(() => {
    const filtered = rawItems.filter((item) => {
      const query = q.trim().toLowerCase();
      if (!query) return true;
      return (
        item.title.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query) ||
        item.keyValues.some((kv) => kv.value.toLowerCase().includes(query))
      );
    });

    return filtered.sort((a, b) => {
      if (ordering === 'name') return a.title.localeCompare(b.title);
      if (ordering === '-name') return b.title.localeCompare(a.title);
      const aDate = new Date(a.lastUpdated || '').getTime();
      const bDate = new Date(b.lastUpdated || '').getTime();
      return bDate - aDate;
    });
  }, [ordering, q, rawItems]);

  const updateQuery = (next: Record<string, string>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(next).forEach(([key, value]) => {
      if (value) params.set(key, value);
      else params.delete(key);
    });
    router.push(params.toString() ? `${pathname}?${params.toString()}` : pathname);
  };

  return (
    <>
      <div className="govuk-width-container">
        <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <a className="govuk-breadcrumbs__link" href={HOSTS.root}>Bus Open Data Service</a>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/">Find Bus Open Data</Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/data">Browse</Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">{breadcrumbLabel}</li>
          </ol>
        </nav>
      </div>

      <BrowseSearchBanner
        title={title}
        description={description}
        placeholder={placeholder}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        onSearchSubmit={() => updateQuery({ q: searchValue })}
      />

      <div className="govuk-width-container">
        <main className="govuk-main-wrapper" id="main-content" role="main">
          <div className="govuk-grid-row govuk-!-margin-top-4">
            <div className="govuk-grid-column-two-thirds">
              <div className="app-data-browser__results-heading">
                <span className="govuk-body">{filteredAndSorted.length.toLocaleString()} results</span>
              </div>
              <div className="app-data-browser__sort-control">
                <label className="govuk-label" htmlFor="ordering">Sort by</label>
                <select
                  className="govuk-select"
                  id="ordering"
                  value={ordering}
                  onChange={(e) => updateQuery({ ordering: e.target.value })}
                >
                  <option value="-modified">Recently updated</option>
                  <option value="name">Data set name A-Z</option>
                  <option value="-name">Data set name Z-A</option>
                </select>
              </div>

              {error && <p className="govuk-body">{error}</p>}
              {isLoading ? (
                <p className="govuk-body">Loading results...</p>
              ) : (
                filteredAndSorted.map((item, index) => (
                  <div className="app-data-browser__result-item" key={item.id}>
                    {index > 0 && <hr className="app-data-browser__result-divider" />}
                    <DataBrowserResultCard
                      title={item.title}
                      href="#"
                      status={item.status}
                      statusLabel={item.status === 'inactive' ? 'Inactive' : 'Published'}
                      keyValues={item.keyValues}
                      description={item.description}
                    />
                  </div>
                ))
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

