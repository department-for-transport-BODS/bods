/**
 * Organisation Selection Page
 *
 * Allows publishers to select which organisation to work with
 */

'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { getPaginated } from '@/lib/api-client';
import { useAuth } from '@/hooks/useAuth';
import { useRouter, useSearchParams } from 'next/navigation';

interface Organisation {
  id: number;
  name: string;
  short_name?: string;
}

function SelectOrg() {
  const [orgs, setOrgs] = useState<Organisation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const selectedDataType = searchParams.get('dataType');

  const isValidDataType =
    selectedDataType === 'timetable' || selectedDataType === 'avl' || selectedDataType === 'fares';

  useEffect(() => {
    const loadOrganisations = async () => {
      try {
        const data = await getPaginated<Organisation>('/api/publish/organisations/');

        if (data.results.length === 1 && user?.is_single_org_user) {
          const orgId = data.results[0].id;
          router.push(
            isValidDataType
              ? `/publish/org/${orgId}/dataset/${selectedDataType}`
              : `/publish/org/${orgId}/dataset`,
          );
          return;
        }

        setOrgs(data.results);
      } catch (err) {
        console.error('Failed to load organisations', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadOrganisations();
  }, [isValidDataType, router, selectedDataType, user?.is_single_org_user]);

  const handleSelect = (orgId: number) => {
    if (isValidDataType) {
      router.push(`/publish/org/${orgId}/dataset/${selectedDataType}`);
      return;
    }

    // Default to choose data type when no data type is provided.
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
              className="govuk-link govuk-link--no-visited-state app-link-button"
              onClick={() => handleSelect(org.id)}
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
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: '/data' },
            { label: 'Publish Bus Open Data', href: '/publish' },
            { label: 'Select organisation', current: true },
          ]}
        />

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
