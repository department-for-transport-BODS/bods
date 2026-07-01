'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DatasetDescriptionFields } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { validateAvlDescriptionStep } from '@/lib/validation/avl-publish';

interface DatasetEditResponse {
  datasetId: number;
  name: string;
  description: string;
  shortDescription: string;
}

function AvlDatasetEditContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const detailUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}`;
  const listUrl = `/publish/org/${orgId}/dataset/avl`;
  const editUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/dataset-edit`;

  const [feedName, setFeedName] = useState('');
  const [description, setDescription] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadDatasetEdit = async () => {
      setIsLoading(true);
      setSubmitError('');

      try {
        const response = await fetch(`/api/avl/dataset-edit?orgId=${orgId}&datasetId=${datasetId}`, {
          credentials: 'include',
        });

        const data = (await response.json().catch(() => ({}))) as DatasetEditResponse & { error?: string };

        if (!response.ok) {
          if (!cancelled) {
            setSubmitError(data.error || `Unable to load feed details (${response.status})`);
            setIsLoading(false);
          }
          return;
        }

        if (!cancelled) {
          setFeedName(data.name || '');
          setDescription(data.description || '');
          setShortDescription(data.shortDescription || '');
          setIsLoading(false);
        }
      } catch {
        if (!cancelled) {
          setSubmitError('Unable to load feed details. Please try again.');
          setIsLoading(false);
        }
      }
    };

    loadDatasetEdit();

    return () => {
      cancelled = true;
    };
  }, [datasetId, orgId]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validationErrors = validateAvlDescriptionStep({ description, shortDescription });
    setErrors(validationErrors);
    setSubmitError('');

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.set('description', description);
      formData.set('short_description', shortDescription);

      const response = await fetch(`/api/avl/dataset-edit?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      const data = (await response.json().catch(() => ({}))) as {
        redirect?: string;
        error?: string;
        fieldErrors?: Record<string, string[] | string>;
        field_errors?: Record<string, string[] | string>;
      };

      if (!response.ok) {
        const nextErrors: Record<string, string> = {};
        const fieldErrors = data.fieldErrors || data.field_errors || {};

        const descriptionError = fieldErrors.description;
        if (descriptionError) {
          nextErrors.description = Array.isArray(descriptionError) ? descriptionError[0] : descriptionError;
        }

        const shortDescriptionError = fieldErrors.short_description;
        if (shortDescriptionError) {
          nextErrors.shortDescription = Array.isArray(shortDescriptionError)
            ? shortDescriptionError[0]
            : shortDescriptionError;
        }

        if (Object.keys(nextErrors).length > 0) {
          setErrors(nextErrors);
        } else {
          setSubmitError(data.error || `Unable to save feed description (${response.status})`);
        }

        setIsSubmitting(false);
        return;
      }

      globalThis.location.href = data.redirect || detailUrl;
    } catch {
      setSubmitError('An error occurred while saving. Please try again.');
      setIsSubmitting(false);
    }
  };

  const summaryErrors = [
    errors.description ? { text: errors.description, href: '#id_description' } : null,
    errors.shortDescription ? { text: errors.shortDescription, href: '#id_short_description' } : null,
  ].filter((error): error is { text: string; href: string } => error !== null);

  const breadcrumbFeedName =
    feedName.length > 20 ? `${feedName.slice(0, 19)}...` : feedName || `Feed ${datasetId}`;

  if (isLoading) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <p className="govuk-body">Loading edit form...</p>
        </div>
      </div>
    );
  }

  if (submitError && !feedName && !description && !shortDescription) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-error-summary" role="alert">
            <h2 className="govuk-error-summary__title">Unable to load edit page</h2>
            <div className="govuk-error-summary__body">
              <p className="govuk-body">{submitError}</p>
              <Link className="govuk-link" href={detailUrl}>
                Back to feed details
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="govuk-width-container">
      <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
        <ol className="govuk-breadcrumbs__list">
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/">
              Bus Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href="/publish/">
              Publish Open Data Service
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href={listUrl}>
              Your data feed
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item">
            <Link className="govuk-breadcrumbs__link" href={detailUrl}>
              {breadcrumbFeedName}
            </Link>
          </li>
          <li className="govuk-breadcrumbs__list-item" aria-current="page">
            <Link className="govuk-breadcrumbs__link" href={editUrl}>
              Edit description
            </Link>
          </li>
        </ol>
      </nav>

      <div className="govuk-main-wrapper">

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
            {summaryErrors.length > 0 && <ErrorSummary errors={summaryErrors} summaryId="avl-edit-description-error-title" />}
            {submitError && <ErrorSummary errors={[submitError]} summaryId="avl-edit-description-submit-error-title" />}

            <h1 className="govuk-heading-l">Edit description</h1>

            <form method="post" onSubmit={onSubmit} noValidate>
              <DatasetDescriptionFields
                description={description}
                shortDescription={shortDescription}
                descriptionLabel="Data feed description"
                shortDescriptionLabel="Data feed short description"
                showShortDescriptionCounter={false}
                errors={{ description: errors.description, shortDescription: errors.shortDescription }}
                descriptionHint="The info will give context to data feed users. Please be descriptive but do not use personally identifiable information. Information you may wish to include: time & date of feed connection, reason for updating feed, OpCo/region/zone of feed, services included in feed."
                shortDescriptionHint="This info will be displayed on your published data feed dashboard to identify this feed and will not be visible to data feed users. The maximum number of characters (with spaces) is 30 characters."
                descriptionClassName="govuk-!-width-three-quarters"
                shortDescriptionClassName="govuk-!-width-three-quarters"
                onDescriptionChange={(value) => {
                  setDescription(value);
                  setErrors((prev) => ({ ...prev, description: '' }));
                }}
                onShortDescriptionChange={(value) => {
                  setShortDescription(value);
                  setErrors((prev) => ({ ...prev, shortDescription: '' }));
                }}
              />

              <div className="govuk-button-group">
                <button type="submit" className="govuk-button" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Save and continue'}
                </button>
                <Link role="button" className="govuk-button govuk-button--secondary" href={detailUrl}>
                  Cancel
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AvlDatasetEditPage() {
  return (
    <ProtectedRoute>
      <AvlDatasetEditContent />
    </ProtectedRoute>
  );
}
