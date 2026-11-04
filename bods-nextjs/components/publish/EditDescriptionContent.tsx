'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay, ErrorSummary, LoadingSpinner } from '@/components/shared';
import { publishPath } from '@/config/client';
import { useApiResource } from '@/hooks/useApiResource';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  validateEditDescription,
  type EditDescriptionErrors,
} from '@/lib/validation/edit-description';

export type EditDescriptionDatasetType = 'timetable' | 'fares';

/** `live` is Django's dataset-edit view, `draft` its revision-edit view. */
export type EditDescriptionMode = 'live' | 'draft';

interface EditDescriptionResponse {
  datasetId: number;
  name: string;
  description: string;
  shortDescription: string;
  isRevisionUpdate: boolean;
}

interface EditDescriptionContentProps {
  datasetType: EditDescriptionDatasetType;
  mode: EditDescriptionMode;
}

const API_TYPE: Record<EditDescriptionDatasetType, string> = {
  timetable: 'timetables',
  fares: 'fares',
};

const API_MODE: Record<EditDescriptionMode, string> = {
  live: 'dataset-edit',
  draft: 'revision-edit',
};

const ERROR_ANCHORS = {
  description: '#id_description',
  shortDescription: '#id_short_description',
};

const DESCRIPTION_HINT =
  'This info will give context to data set users. Please be descriptive but do not use personally identifiable information. Information you may wish to include: The original file name, start date of data, description of timetables, OpCo, locations/region, routes/service numbers for which the data applies, or any other useful high-level information.';

const SHORT_DESCRIPTION_HINT =
  'This information will be displayed on your published data set dashboard to identify this data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 characters.';

function returnPath(datasetPath: string, mode: EditDescriptionMode, isRevisionUpdate: boolean) {
  if (mode === 'live') {
    return `${datasetPath}/`;
  }
  return isRevisionUpdate ? `${datasetPath}/update/review/` : `${datasetPath}/review/`;
}

interface EditDescriptionFormProps {
  initial: EditDescriptionResponse;
  saveUrl: string;
  returnUrl: string;
}

function EditDescriptionForm({ initial, saveUrl, returnUrl }: EditDescriptionFormProps) {
  const router = useRouter();
  const { isSubmitting, submitError, handleSubmit } = useFormSubmit();
  const [description, setDescription] = useState(initial.description);
  const [shortDescription, setShortDescription] = useState(initial.shortDescription);
  const [errors, setErrors] = useState<EditDescriptionErrors>({});

  const summaryItems = submitError ? [submitError] : errorSummaryItems({ ...errors }, ERROR_ANCHORS);
  const hasSummary = summaryItems.length > 0;

  useEffect(() => {
    if (hasSummary) {
      document.querySelector<HTMLElement>('.govuk-error-summary')?.focus();
    }
  }, [errors, submitError, hasSummary]);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateEditDescription({ description, shortDescription });
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    void handleSubmit(async () => {
      const body = new FormData();
      body.set('description', description);
      body.set('short_description', shortDescription);
      try {
        await api.post(saveUrl, body);
      } catch (error) {
        if (error instanceof ApiError && Object.keys(error.fieldErrors).length > 0) {
          const fieldErrors = error.firstFieldErrors();
          setErrors({
            description: fieldErrors.description,
            shortDescription: fieldErrors.short_description,
          });
          return;
        }
        throw error;
      }
      router.push(returnUrl);
    });
  };

  return (
    <form method="post" noValidate onSubmit={onSubmit}>
      {hasSummary && (
        <ErrorSummary errors={summaryItems} tabIndex={-1} dataModule="govuk-error-summary" />
      )}
      <h1 className="govuk-heading-xl">Edit description</h1>
      <div className={`govuk-form-group${errors.description ? ' govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_description">
          Data set description
        </label>
        <span id="id_description-hint" className="govuk-hint">
          {DESCRIPTION_HINT}
        </span>
        {errors.description && (
          <span id="1_id_description-error" className="govuk-error-message">
            {errors.description}
          </span>
        )}
        <textarea
          name="description"
          cols={40}
          rows={3}
          placeholder=""
          className={`govuk-!-width-three-quarters govuk-textarea${errors.description ? ' govuk-textarea--error' : ''}`}
          aria-describedby="id_description-hint"
          required
          id="id_description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </div>
      <div className={`govuk-form-group${errors.shortDescription ? ' govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_short_description">
          Data set short description
        </label>
        <span id="id_short_description-hint" className="govuk-hint">
          {SHORT_DESCRIPTION_HINT}
        </span>
        {errors.shortDescription && (
          <span id="1_id_short_description-error" className="govuk-error-message">
            {errors.shortDescription}
          </span>
        )}
        <input
          type="text"
          name="short_description"
          maxLength={30}
          placeholder=""
          className={`govuk-!-width-three-quarters govuk-input${errors.shortDescription ? ' govuk-input--error' : ''}`}
          size={30}
          aria-describedby="id_short_description-hint"
          required
          id="id_short_description"
          value={shortDescription}
          onChange={(event) => setShortDescription(event.target.value)}
        />
      </div>
      <div className="button-holder">
        <button
          type="submit"
          name="submit"
          value="submit"
          className="govuk-button"
          data-module="govuk-button"
          disabled={isSubmitting}
        >
          Save and continue
        </button>
        <button
          type="button"
          name="cancel"
          value="cancel"
          className="govuk-button govuk-button--secondary"
          data-module="govuk-button"
          onClick={() => router.push(returnUrl)}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function EditDescriptionContent({ datasetType, mode }: EditDescriptionContentProps) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const apiUrl = `/api/publish/${API_TYPE[datasetType]}/${API_MODE[mode]}/${orgId}/${datasetId}/`;

  const fetchContext = useCallback(() => api.get<EditDescriptionResponse>(apiUrl), [apiUrl]);
  const { data, isLoading, error } = useApiResource(fetchContext, 'Unable to load data set details');

  const datasetPath = `/org/${orgId}/dataset/${datasetType}/${datasetId}`;
  const returnUrl = publishPath(returnPath(datasetPath, mode, Boolean(data?.isRevisionUpdate)));

  return (
    <div className="govuk-width-container">
      {data && (
        <Breadcrumbs
          items={hostBreadcrumbs(
            'publish',
            { label: 'Your data sets', href: publishPath(`/org/${orgId}/dataset/${datasetType}/`) },
            { label: data.name, href: returnUrl, truncateAt: 20 },
            { label: 'Edit description', href: publishPath(`${datasetPath}/dataset-edit/`) },
          )}
        />
      )}
      <div className="govuk-main-wrapper">
        {isLoading && <LoadingSpinner />}
        {!isLoading && error && <ErrorDisplay message={error} />}
        {data && (
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
              <div className="component-wrapper">
                <EditDescriptionForm initial={data} saveUrl={`${apiUrl}save/`} returnUrl={returnUrl} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
