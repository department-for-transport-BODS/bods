'use client';

import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';
import { useApiResource } from '@/hooks/useApiResource';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import { PublishStepper, type StepState } from '@/components/publish';
import { ErrorSummary } from '@/components/shared/ErrorSummary';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import {
  DateFields,
  OperatingDatesHeading,
  SEASONAL_SERVICE_HEADING,
  SeasonalServiceBreadcrumbs,
  addNewPath,
  pageQuery,
  seasonalServicesApiPath,
  seasonalServicesListPath,
  type SeasonalServiceOrganisation,
} from './shared';

interface LicencesResponse extends SeasonalServiceOrganisation {
  licences: { id: number; number: string }[];
}

type Step = 1 | 2;

const LICENCE_ID = 'id_select_psv_licence_number-licence';
const CODE_ID = 'id_provide_operating_dates-registration_code';
const START_ID = 'id_provide_operating_dates-start';
const END_ID = 'id_provide_operating_dates-end';

const ERROR_ANCHORS: Record<string, string> = {
  licence: `#${LICENCE_ID}`,
  registrationCode: `#${CODE_ID}`,
  start: `#${START_ID}`,
  end: `#${END_ID}`,
};

const STEP_LABELS = ['1. Select PSV licence number', '2. Provide operating dates'];

export function SeasonalServiceAddNewContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const page = searchParams.get('page');

  const [step, setStep] = useState<Step>(1);
  const [licenceId, setLicenceId] = useState('');
  const [licenceNumber, setLicenceNumber] = useState('');
  const [registrationCode, setRegistrationCode] = useState('');
  const [dates, setDates] = useState({ start: '', end: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { isSubmitting, submitError, handleSubmit, clearError } = useFormSubmit();

  const loadLicences = useCallback(
    () => api.get<LicencesResponse>(seasonalServicesApiPath(orgId, 'licences/')),
    [orgId],
  );
  const { data, isLoading, error } = useApiResource<LicencesResponse>(
    loadLicences,
    'Unable to load seasonal service licences.',
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
          <ErrorDisplay message={error || 'Unable to load seasonal service licences.'} />
        </div>
      </div>
    );
  }

  const cancelHref = `${seasonalServicesListPath(orgId)}${pageQuery(page)}`;

  const applyApiError = (err: unknown) => {
    if (err instanceof ApiError && err.hasFieldErrors) {
      setErrors(err.firstFieldErrors());
      return;
    }
    throw err;
  };

  const submitLicence = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearError();
    void handleSubmit(async () => {
      try {
        const response = await api.post<{ licence: { id: number; number: string } }>(
          seasonalServicesApiPath(orgId, 'validate-licence/'),
          { licence: licenceId },
        );
        setLicenceNumber(response.licence.number);
        setErrors({});
        setStep(2);
      } catch (err) {
        applyApiError(err);
      }
    });
  };

  const submitDates = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearError();
    void handleSubmit(async () => {
      try {
        await api.post(seasonalServicesApiPath(orgId, 'create/'), {
          licence: licenceId,
          registrationCode,
          start: dates.start,
          end: dates.end,
        });
        router.push(cancelHref);
      } catch (err) {
        applyApiError(err);
      }
    });
  };

  // Django's "Edit" link restarts the wizard from the licence step.
  const restart = () => {
    setStep(1);
    setLicenceId('');
    setLicenceNumber('');
    setRegistrationCode('');
    setDates({ start: '', end: '' });
    setErrors({});
    clearError();
  };

  const steps = STEP_LABELS.map((label, index) => {
    const stepNumber = index + 1;
    let state: StepState = 'next';
    if (stepNumber < step) state = 'previous';
    else if (stepNumber === step) state = 'selected';
    return { label, state };
  });

  const buttons = (primaryLabel: string) => (
    <div className="button-holder buttons">
      <button type="submit" name="submit" value="submit" className="govuk-button" data-module="govuk-button" disabled={isSubmitting}>
        {primaryLabel}
      </button>
      <Link className="govuk-button govuk-button--secondary" href={cancelHref}>
        Cancel
      </Link>
    </div>
  );

  return (
    <div className="seasonal-services-page">
      <SeasonalServiceBreadcrumbs
        orgId={orgId}
        organisation={data}
        extra={{ label: 'Add new', href: addNewPath(orgId) }}
        stepper={
          <div className="govuk-breadcrumbs">
            <PublishStepper steps={steps} />
          </div>
        }
      />

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <h1 className="govuk-heading-xl">{SEASONAL_SERVICE_HEADING}</h1>
              {step === 1 && (
                <p className="govuk-body govuk-!-margin-bottom-8">
                  Select the PSV licence number to add seasonal service operating dates.
                </p>
              )}
            </div>
          </div>
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-one-half">
              {step === 1 ? (
                <form className="seasonal-service" method="post" noValidate onSubmit={submitLicence}>
                  <ErrorSummary
                    errors={errorSummaryItems(errors, ERROR_ANCHORS)}
                    tabIndex={-1}
                    dataModule="govuk-error-summary"
                  />
                  <div className="licence">
                    <div className={`govuk-form-group  ${errors.licence ? 'govuk-form-group--error' : ''}`}>
                      <label className="govuk-label" htmlFor={LICENCE_ID}>
                        PSV licence number
                      </label>
                      {errors.licence && (
                        <span id={`1_${LICENCE_ID}-error`} className="govuk-error-message">
                          {errors.licence}
                        </span>
                      )}
                      <div className="select-wrapper">
                        <select
                          name="select_psv_licence_number-licence"
                          className="govuk-!-width-full govuk-select "
                          required
                          id={LICENCE_ID}
                          value={licenceId}
                          onChange={(event) => setLicenceId(event.target.value)}
                        >
                          <option value="">Select PSV licence number</option>
                          {data.licences.map((licence) => (
                            <option key={licence.id} value={licence.id}>
                              {licence.number}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                  <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible" />
                  {buttons('Continue')}
                </form>
              ) : (
                <form className="seasonal-service" method="post" noValidate onSubmit={submitDates}>
                  <ErrorSummary
                    errors={errorSummaryItems(errors, ERROR_ANCHORS)}
                    tabIndex={-1}
                    dataModule="govuk-error-summary"
                  />
                  <div className="heading-container">
                    <h2 className="govuk-heading-s govuk-!-margin-bottom-2">PSV Licence Number</h2>
                    <a
                      className="govuk-link govuk-!-font-size-19"
                      href={addNewPath(orgId)}
                      onClick={(event) => {
                        event.preventDefault();
                        restart();
                      }}
                    >
                      Edit
                    </a>
                  </div>
                  <p className="govuk-body">{licenceNumber}</p>
                  <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible govuk-!-margin-bottom-6 govuk-!-margin-top-6" />
                  <div className={`govuk-form-group${errors.registrationCode ? ' govuk-form-group--error' : ''}`}>
                    <label className="govuk-label" htmlFor={CODE_ID}>
                      Service code
                    </label>
                    {errors.registrationCode && (
                      <span id={`1_${CODE_ID}-error`} className="govuk-error-message">
                        {errors.registrationCode}
                      </span>
                    )}
                    <div className={`service-code-widget${errors.registrationCode ? ' govuk-input--error' : ''}`}>
                      <p>{licenceNumber}/</p>
                      <input
                        type="number"
                        required
                        name="provide_operating_dates-registration_code"
                        className={`govuk-input${errors.registrationCode ? ' govuk-input--error' : ''}`}
                        id={CODE_ID}
                        value={registrationCode}
                        onChange={(event) => setRegistrationCode(event.target.value)}
                      />
                    </div>
                  </div>
                  <OperatingDatesHeading />
                  <DateFields
                    idPrefix="provide_operating_dates-"
                    startName="provide_operating_dates-start"
                    endName="provide_operating_dates-end"
                    values={dates}
                    errors={{ start: errors.start, end: errors.end }}
                    onChange={(field, value) => setDates((current) => ({ ...current, [field]: value }))}
                  />
                  <hr className="govuk-section-break govuk-section-break--xs govuk-section-break--visible" />
                  {buttons('Save')}
                </form>
              )}
              {submitError && <p className="govuk-error-message">{submitError}</p>}
              <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
