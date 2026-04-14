/**
 * Organisation Selection Page
 * 
 * Allows publishers to select which organisation to work with
 */

'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { getPaginated } from '@/lib/api-client';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';

interface Organisation {
  id: number;
  name: string;
  short_name?: string;
}

function SelectOrg() {
  const [orgs, setOrgs] = useState<Organisation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    loadOrganisations();
  }, []);

  useEffect(() => {
    // Regular org users (non-agents) have exactly one org and should never land here.
    // Redirect them immediately to choose data type.
    if (user && user.is_org_user && !user.is_agent_user && user.organisation_id) {
      router.push(`/publish/org/${user.organisation_id}/dataset`);
      return;
    }

    if (isLoading) {
      return;
    }

    // For agents: if they only have one org, skip selection too.
    if (orgs.length === 1) {
      router.push(`/publish/org/${orgs[0].id}/dataset`);
    }
  }, [isLoading, orgs, router, user]);

  const loadOrganisations = async () => {
    try {
      // Use the v2 operators endpoint, which is the active paginated org list API.
      const data = await getPaginated<Organisation>('/api/v2/operators/');
      setOrgs(data.results);
    } catch (err) {
      console.error('Failed to load organisations', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = (orgId: number) => {
    router.push(`/publish/org/${orgId}/dataset`);
  };

  const renderOrganisations = () => {
    if (isLoading) {
      return <p className="govuk-body">Loading organisations...</p>;
    }

    if (orgs.length === 0) {
      return <p className="govuk-body">No organisations found for this account.</p>;
    }

    return (
      <ul className="govuk-list">
        {orgs.map((org) => (
          <li key={org.id}>
            <button
              className="govuk-link govuk-link--no-visited-state"
              onClick={() => handleSelect(org.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
            >
              {org.name}
            </button>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/data">
                Bus Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/publish">
                Publish Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">
              Select organisation
            </li>
          </ol>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Select organisation</h1>

            {renderOrganisations()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SelectOrgPage() {
  return (
    <ProtectedRoute>
      <SelectOrg />
    </ProtectedRoute>
  );
}

