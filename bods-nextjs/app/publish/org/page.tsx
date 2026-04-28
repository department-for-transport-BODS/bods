/**
 * Organisation Selection Page
 * 
 * Allows publishers to select which organisation to work with
 */

'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { getPaginated } from '@/lib/api-client';
import { useRouter, useSearchParams } from 'next/navigation';

interface Organisation {
  id: number;
  name: string;
  short_name?: string;
}

function SelectOrg() {
  const [orgs, setOrgs] = useState<Organisation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const searchParams = useSearchParams();

  const selectedDataType = searchParams.get('dataType');

  const isValidDataType =
    selectedDataType === 'timetable' || selectedDataType === 'avl' || selectedDataType === 'fares';

  useEffect(() => {
    loadOrganisations();
  }, []);

  const loadOrganisations = async () => {
    try {
      const data = await getPaginated<Organisation>('/api/organisations/');
      setOrgs(data.results);
    } catch (err) {
      console.error('Failed to load organisations', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = (orgId: number) => {
    if (isValidDataType) {
      router.push(`/publish/org/${orgId}/dataset/${selectedDataType}`);
      return;
    }

    // Default to timetables when no data type is provided.
    router.push(`/publish/org/${orgId}/dataset/timetable`);
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Select organisation</h1>

            {isLoading ? (
              <p className="govuk-body">Loading organisations...</p>
            ) : (
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
            )}
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

