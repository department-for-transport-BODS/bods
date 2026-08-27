'use client';

/**
 * Organisation profile (view)
 *
 * Mirrors Django's organisation/org_profile.html: short name, licence
 * requirement, NOC codes, licence numbers, and service code exemptions.
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { HOSTS, publishAppPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';

interface ServiceCodeExemption {
  registrationNumber: string;
  justification: string;
}

interface OrganisationProfile {
  id: number;
  name: string;
  shortName: string;
  licenceRequired: boolean | null;
  nocs: string[];
  licenceNumbers: string[];
  canEdit: boolean;
  serviceCodeExemptions: ServiceCodeExemption[];
}

function OrganisationProfileContent() {
  const params = useParams();
  const orgId = params.orgId as string;

  const [profile, setProfile] = useState<OrganisationProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<OrganisationProfile>(`/api/publish/organisation/profile/${orgId}/`)
      .then((data) => {
        if (!isCancelled) setProfile(data);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load this organisation profile.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [orgId]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'My account', href: publishAppPath('/account') },
            { label: 'Organisation profile', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && profile && (
              <>
                <h1 className="govuk-heading-xl">{profile.name}</h1>

                <dl className="govuk-summary-list">
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Short name</dt>
                    <dd className="govuk-summary-list__value">{profile.shortName || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">PSV licence required</dt>
                    <dd className="govuk-summary-list__value">{profile.licenceRequired ? 'Yes' : 'No'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">National Operator Codes</dt>
                    <dd className="govuk-summary-list__value">
                      {profile.nocs.length > 0 ? profile.nocs.join(', ') : '-'}
                    </dd>
                  </div>
                  {profile.licenceRequired && (
                    <div className="govuk-summary-list__row">
                      <dt className="govuk-summary-list__key">PSV licence numbers</dt>
                      <dd className="govuk-summary-list__value">
                        {profile.licenceNumbers.length > 0 ? profile.licenceNumbers.join(', ') : '-'}
                      </dd>
                    </div>
                  )}
                </dl>

                {profile.canEdit && (
                  <Link className="govuk-button" href={publishAppPath(`/org/${orgId}/profile/edit`)}>
                    Edit organisation profile
                  </Link>
                )}

                {profile.serviceCodeExemptions.length > 0 && (
                  <>
                    <h2 className="govuk-heading-m">Service code exemptions</h2>
                    <table className="govuk-table">
                      <thead className="govuk-table__head">
                        <tr className="govuk-table__row">
                          <th className="govuk-table__header" scope="col">Registration number</th>
                          <th className="govuk-table__header" scope="col">Justification</th>
                        </tr>
                      </thead>
                      <tbody className="govuk-table__body">
                        {profile.serviceCodeExemptions.map((exemption) => (
                          <tr key={exemption.registrationNumber} className="govuk-table__row">
                            <td className="govuk-table__cell">{exemption.registrationNumber}</td>
                            <td className="govuk-table__cell">{exemption.justification || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OrganisationProfilePage() {
  return (
    <ProtectedRoute>
      <OrganisationProfileContent />
    </ProtectedRoute>
  );
}
