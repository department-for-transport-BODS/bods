'use client';

/**
 * Organisation profile (edit)
 *
 * Mirrors Django's OrganisationProfileForm.
 * `pk` is the organisation id (`/account/manage/org-profile/<org_id>/edit`).
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api, getCsrfToken } from '@/lib/api-client';

interface OrganisationProfile {
  id: number;
  shortName: string;
  licenceRequired: boolean | null;
  nocs: string[];
  licenceNumbers: string[];
}

function DynamicListField({
  label,
  values,
  onChange,
  placeholder,
}: Readonly<{
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder: string;
}>) {
  const items = values.length > 0 ? values : [''];

  const updateAt = (index: number, value: string) => {
    const next = [...items];
    next[index] = value;
    onChange(next);
  };

  return (
    <div className="govuk-form-group">
      <label className="govuk-label">{label}</label>
      {items.map((value, index) => (
        <div key={`${label}-${index}`} className="govuk-!-margin-bottom-2 govuk-button-group">
          <input
            className="govuk-input govuk-!-width-one-third"
            type="text"
            value={value}
            placeholder={placeholder}
            onChange={(e) => updateAt(index, e.target.value)}
          />
          <button
            type="button"
            className="govuk-button govuk-button--secondary"
            onClick={() => onChange(items.filter((_, i) => i !== index))}
          >
            Remove
          </button>
        </div>
      ))}
      <button type="button" className="govuk-button govuk-button--secondary" onClick={() => onChange([...items, ''])}>
        Add another
      </button>
    </div>
  );
}

function OrganisationProfileEditContent() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.pk as string;
  const profileUrl = `/account/manage/org-profile/${orgId}`;

  const [shortName, setShortName] = useState('');
  const [licenceRequired, setLicenceRequired] = useState(false);
  const [nocs, setNocs] = useState<string[]>([]);
  const [licenceNumbers, setLicenceNumbers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    let isCancelled = false;

    api
      .get<OrganisationProfile>(`/api/publish/organisation/profile/${orgId}/`)
      .then((data) => {
        if (isCancelled) return;
        setShortName(data.shortName || '');
        setLicenceRequired(Boolean(data.licenceRequired));
        setNocs(data.nocs);
        setLicenceNumbers(data.licenceNumbers);
      })
      .catch(() => {
        if (!isCancelled) setErrors({ form: 'Unable to load this organisation profile.' });
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [orgId]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await fetch(`/api/publish/organisation/profile/${orgId}/update/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({
          shortName,
          licenceRequired,
          nocs: nocs.filter((noc) => noc.trim()),
          licenceNumbers: licenceNumbers.filter((num) => num.trim()),
        }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const fieldErrors = data.field_errors || {};
        setErrors({
          shortName: fieldErrors.shortName?.[0],
          licenceRequired: fieldErrors.licenceRequired?.[0],
          licenceNumbers: fieldErrors.licenceNumbers?.[0],
          form: !data.field_errors ? data.error || 'Unable to save this profile.' : '',
        });
        setIsSubmitting(false);
        return;
      }

      router.push(profileUrl);
      router.refresh();
    } catch {
      setErrors({ form: 'Unable to save this profile.' });
      setIsSubmitting(false);
    }
  };

  const summaryErrors = Object.values(errors).filter(Boolean) as string[];

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'Organisation profile', href: profileUrl },
            { label: 'Edit', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Edit organisation profile</h1>

            {isLoading && <p className="govuk-body">Loading...</p>}

            {!isLoading && (
              <form onSubmit={handleSubmit} noValidate>
                {summaryErrors.length > 0 && (
                  <ErrorSummary errors={summaryErrors} summaryId="org-profile-edit-error-title" />
                )}

                <div className="govuk-form-group">
                  <label className="govuk-label" htmlFor="short_name">Organisation short name</label>
                  <input
                    className="govuk-input"
                    id="short_name"
                    type="text"
                    value={shortName}
                    onChange={(e) => setShortName(e.target.value)}
                  />
                </div>

                <div className="govuk-checkboxes__item">
                  <input
                    className="govuk-checkboxes__input"
                    id="licence_not_required"
                    type="checkbox"
                    checked={!licenceRequired}
                    onChange={(e) => setLicenceRequired(!e.target.checked)}
                  />
                  <label className="govuk-label govuk-checkboxes__label" htmlFor="licence_not_required">
                    I do not have a PSV Licence number
                  </label>
                </div>

                <DynamicListField
                  label="National Operator Codes"
                  values={nocs}
                  onChange={setNocs}
                  placeholder="e.g. ABCD"
                />

                {licenceRequired && (
                  <DynamicListField
                    label="PSV licence numbers"
                    values={licenceNumbers}
                    onChange={setLicenceNumbers}
                    placeholder="e.g. AB1234567"
                  />
                )}

                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : 'Save'}
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(profileUrl)}>
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OrganisationProfileEditPage() {
  return (
    <ProtectedRoute>
      <OrganisationProfileEditContent />
    </ProtectedRoute>
  );
}
