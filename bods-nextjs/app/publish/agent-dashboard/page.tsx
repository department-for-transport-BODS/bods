/**
 * Agent Dashboard
 *
 * Lists every organisation the signed-in agent/org user belongs to, with
 * per-type requires-attention counts.
 * 
 * Source AgentDashboardView (transit_odp/publish/views/navigation.py)
 */
'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';
import { HOSTS } from '@/config/client';

interface AgentOrganisation {
  id: number;
  name: string;
  requiresAttention: number;
  avlRequiresAttention: number;
  faresRequiresAttention: number;
}

interface AgentDashboardResponse {
  results: AgentOrganisation[];
}

function AgentDashboard() {
  const [searchInput, setSearchInput] = useState('');
  const [query, setQuery] = useState('');
  const [organisations, setOrganisations] = useState<AgentOrganisation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const loadOrganisations = async () => {
      setIsLoading(true);
      setError('');

      try {
        const data = await api.get<AgentDashboardResponse>(
          `/api/publish/agent-dashboard/organisations/?q=${encodeURIComponent(query)}`,
        );

        if (!isCancelled) {
          setOrganisations(Array.isArray(data.results) ? data.results : []);
        }
      } catch {
        if (!isCancelled) {
          setError('Unable to load your organisations here. You can continue in the Django list view.');
          setOrganisations([]);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    loadOrganisations();

    return () => {
      isCancelled = true;
    };
  }, [query]);

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setQuery(searchInput.trim());
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'Agent Dashboard', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-three-quarters">
            <h1 className="govuk-heading-xl">Agent Dashboard</h1>
            <p className="govuk-body-m">
              You can choose an operator to view or publish data by clicking the operator name below.
            </p>

            <form onSubmit={handleSearchSubmit}>
              <div className="govuk-grid-column-three-quarters govuk-!-padding-left-0">
                <div className="searchbox">
                  <input
                    className="searchbox__input"
                    id="search"
                    name="q"
                    type="search"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Enter an operator name"
                  />
                  <button className="searchbox__button" type="submit" aria-label="submit search">
                    Search
                  </button>
                </div>
              </div>
            </form>

            {isLoading && <p className="govuk-body">Loading organisations...</p>}

            {!isLoading && error && <p className="govuk-body-m">{error}</p>}

            {!isLoading && !error && organisations.length > 0 && (
              <table className="govuk-table agent_dashboard">
                <thead className="govuk-table__head">
                  <tr className="govuk-table__row">
                    <th className="govuk-table__header govuk-!-width-one-quarter" scope="col">
                      Organisation
                    </th>
                    <th className="govuk-table__header govuk-!-width-one-quarter" scope="col">
                      Timetables services requiring attention
                    </th>
                    <th className="govuk-table__header govuk-!-width-one-quarter" scope="col">
                      Location services requiring attention
                    </th>
                    <th className="govuk-table__header govuk-!-width-one-quarter" scope="col">
                      Fares services requiring attention
                    </th>
                  </tr>
                </thead>
                <tbody className="govuk-table__body">
                  {organisations.map((organisation) => (
                    <tr key={organisation.id} className="govuk-table__row">
                      <td className="govuk-table__cell govuk-!-font-weight-bold">
                        <Link
                          className="govuk-link"
                          href={`/publish/org/${organisation.id}/dataset/timetable`}
                        >
                          {organisation.name}
                        </Link>
                      </td>
                      <td className="govuk-table__cell">{organisation.requiresAttention}</td>
                      <td className="govuk-table__cell">{organisation.avlRequiresAttention}</td>
                      <td className="govuk-table__cell">{organisation.faresRequiresAttention}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {!isLoading && !error && organisations.length === 0 && query && (
              <>
                <h2 className="govuk-heading-m">Sorry, no results found for your search</h2>
                <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
                <p className="govuk-body">
                  <b>Having trouble finding what you want?</b>
                </p>
                <ul className="govuk-list govuk-list--bullet">
                  <li>Check your spelling and try again</li>
                  <li>Use another search term</li>
                </ul>
              </>
            )}

            {!isLoading && !error && organisations.length === 0 && !query && (
              <>
                <p className="govuk-body-l">
                  You don&apos;t have any operators yet to act as an agent on behalf of. Please go to My
                  Account section to set-up an operator
                </p>
                <Link href="/account" className="govuk-button govuk-button--start">
                  Go to My Account
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentDashboardPage() {
  return (
    <ProtectedRoute>
      <AgentDashboard />
    </ProtectedRoute>
  );
}
