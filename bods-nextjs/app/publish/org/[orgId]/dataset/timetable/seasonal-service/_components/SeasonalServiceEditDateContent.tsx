'use client';

import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';
import { useApiResource } from '@/hooks/useApiResource';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import { ErrorSummary } from '@/components/shared/ErrorSummary';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { publishAppPath } from '@/config/client';
import {
  DateFields,
  OperatingDatesHeading,
  SEASONAL_SERVICE_HEADING,
  SeasonalServiceBreadcrumbs,
  pageQuery,
  seasonalServicesApiPath,
  seasonalServicesListPath,
  type SeasonalServiceOrganisation,
  type SeasonalServiceRow,
} from './shared';

type SeasonalServiceDetail = SeasonalServiceOrganisation & SeasonalServiceRow;

const ERROR_ANCHORS: Record<string, string> = {
  start: '#id_start',
  end: '#id_end',
};

export function SeasonalServiceEditDateContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const serviceId = params.serviceId as string;
  const page = searchParams.get('page');

  const [dates, setDates] = useState<{ start: string; end: string } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { isSubmitting, submitError, handleSubmit, clearError } = useFormSubmit();

  const loadService = useCallback(
    () => api.get<SeasonalServiceDetail>(seasonalServicesApiPath(orgId, `${encodeURIComponent(serviceId)}/`)),
    [orgId, serviceId],
  );
  const { data, isLoading, error } = useApiResource<SeasonalServiceDetail>(
    loadService,
    'Unable to load seasonal service.',
  );

  const hasErrors = Object.keys(errors).length > 0;
  useEffect(() => {
    document.title = hasErrors ? 'Error: Bus Open Data Service' : 'Bus Open Data Service';
  }, [hasErrors]);

  if (isLoading && !data) {
    return <LoadingSpinner message="Loading" />;
  }

  if (error || !data) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <ErrorDisplay message={error || 'Unable to load seasonal service.'} />
        </div>
      </div>
    );
  }

  const values = dates ?? { start: data.start, end: data.end };
  const listHref = `${seasonalServicesListPath(orgId)}${pageQuery(page)}`;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearError();
    void handleSubmit(async () => {
      try {
        await api.post(seasonalServicesApiPath(orgId, `${encodeURIComponent(serviceId)}/update/`), values);
        router.push(listHref);
      } catch (err) {
        if (err instanceof ApiError && err.hasFieldErrors) {
          setErrors(err.firstFieldErrors());
          return;
        }
        throw err;
      }
    });
  };

  return (
    <div className="seasonal-services-page">
      <SeasonalServiceBreadcrumbs
        orgId={orgId}
        organisation={data}
        extra={{
          label: 'Edit dates',
          href: publishAppPath(`/org/${orgId}/dataset/timetable/seasonal-service/${serviceId}/edit-date`),
        }}
      />

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <h1 className="govuk-heading-xl">{SEASONAL_SERVICE_HEADING}</h1>
            </div>
          </div>
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-one-half">
              <form className="seasonal-service" method="post" noValidate onSubmit={submit}>
                <ErrorSummary
                  errors={errorSummaryItems(errors, ERROR_ANCHORS)}
                  tabIndex={-1}
                  dataModule="govuk-error-summary"
                />
                <div className="heading-container">
                  <h2 className="govuk-heading-s govuk-!-margin-bottom-2">PSV Licence Number</h2>
                </div>
                <p className="govuk-body">{data.licenceNumber}</p>
                <div className="heading-container">
                  <h2 className="govuk-heading-s govuk-!-margin-bottom-2">Service code</h2>
                </div>
                <p className="govuk-body">{data.serviceCode}</p>
                <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible govuk-!-margin-bottom-8 govuk-!-margin-top-8" />
                <OperatingDatesHeading />
                <DateFields
                  idPrefix=""
                  values={values}
                  errors={{ start: errors.start, end: errors.end }}
                  onChange={(field, value) => setDates({ ...values, [field]: value })}
                />
                <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible" />
                <div className="button-holder buttons">
                  <button
                    type="submit"
                    name="submit"
                    value="submit"
                    className="govuk-button"
                    data-module="govuk-button"
                    disabled={isSubmitting}
                  >
                    Save
                  </button>
                  <Link className="govuk-button govuk-button--secondary" href={listHref}>
                    Cancel
                  </Link>
                </div>
              </form>
              {submitError && <p className="govuk-error-message">{submitError}</p>}
              <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
