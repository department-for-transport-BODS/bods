'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DatasetDescriptionFields } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { validateTimetableStep1 } from '@/lib/validation/timetable-publish';

type EditContext = {
  description: string;
  shortDescription: string;
};

function TimetableDatasetEditContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const reviewUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}/review`;
  const [description, setDescription] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'Edit description';
    api.get<EditContext>(`/api/publish/timetables/dataset-edit/${orgId}/${datasetId}/`)
      .then((data) => {
        setDescription(data.description || '');
        setShortDescription(data.shortDescription || '');
      })
      .catch((error: Error) => setErrorMessage(error.message))
      .finally(() => setIsLoading(false));
  }, [datasetId, orgId]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateTimetableStep1({ dataSetDesc: description, shortDesc: shortDescription });
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    setErrorMessage('');
    const formData = new FormData();
    formData.set('description', description);
    formData.set('short_description', shortDescription);
    try {
      const response = await api.post<{ redirect?: string }>(
        `/api/publish/timetables/dataset-edit/${orgId}/${datasetId}/save/`,
        formData,
      );
      globalThis.location.href = response.redirect || reviewUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save description. Please try again.');
      setIsSubmitting(false);
    }
  };

  const summaryErrors = [
    errors.dataSetDesc ? { text: errors.dataSetDesc, href: '#id_description' } : null,
    errors.shortDesc ? { text: errors.shortDesc, href: '#id_short_description' } : null,
  ].filter((error): error is { text: string; href: string } => error !== null);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Edit description</h1>
            <ErrorSummary errors={errorMessage ? [errorMessage] : summaryErrors} summaryId="timetable-edit-error-title" />
            {isLoading ? <p className="govuk-body">Loading edit form...</p> : (
              <form onSubmit={handleSubmit} noValidate>
                <DatasetDescriptionFields
                  description={description}
                  shortDescription={shortDescription}
                  shortDescriptionLabel="Data set short description"
                  descriptionHint="This info will give context to data set users. Please be descriptive but do not use personally identifiable information. Information you may wish to include: The original file name, start date of data, description of timetables, OpCo, locations/region, routes/service numbers for which the data applies, or any other useful high-level information."
                  shortDescriptionHint="This information will be displayed on your published data set dashboard to identify this data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 characters."
                  descriptionClassName="govuk-!-width-three-quarters"
                  shortDescriptionClassName="govuk-!-width-three-quarters"
                  errors={{ description: errors.dataSetDesc, shortDescription: errors.shortDesc }}
                  onDescriptionChange={setDescription}
                  onShortDescriptionChange={setShortDescription}
                />
                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save and continue'}</button>
                  <Link role="button" className="govuk-button govuk-button--secondary" href={reviewUrl}>Cancel</Link>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TimetableDatasetEditPage() {
  return <ProtectedRoute><TimetableDatasetEditContent /></ProtectedRoute>;
}
