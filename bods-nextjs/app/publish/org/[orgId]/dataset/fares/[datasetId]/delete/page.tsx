'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function FaresDeletePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const reviewUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/review`;
  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;

  const handleDelete = async () => {
    setErrorMessage('');
    setIsDeleting(true);

    try {
      const token = globalThis.window
        ? globalThis.window.localStorage.getItem('bods.auth.access')
        : null;

      const response = await fetch(`/api/fares/delete?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const data = (await response.json().catch(() => ({}))) as { error?: string; redirect?: string };

      if (!response.ok) {
        setErrorMessage(data.error || `Delete failed (${response.status}).`);
        setIsDeleting(false);
        return;
      }

      globalThis.location.href = data.redirect || faresListUrl;
    } catch {
      setErrorMessage('Unable to delete data set. Please try again.');
      setIsDeleting(false);
    }
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
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset/fares`}>
                Fares Data Sets
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">
              Delete data set
            </li>
          </ol>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Would you like to delete this data set?</h1>
            <p className="govuk-body-l">
              Please confirm that you would like to delete this data set. Any changes you have made so far will not be saved.
            </p>

            {errorMessage ? (
              <div className="govuk-error-summary" role="alert" aria-labelledby="delete-error-title">
                <h2 className="govuk-error-summary__title" id="delete-error-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    <li>{errorMessage}</li>
                  </ul>
                </div>
              </div>
            ) : null}

            <div className="govuk-button-group">
              <button
                type="button"
                className="govuk-button"
                onClick={handleDelete}
                disabled={isDeleting}
                aria-disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
              <Link className="govuk-button govuk-button--secondary" href={reviewUrl}>
                Cancel
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresDeletePage() {
  return (
    <ProtectedRoute>
      <FaresDeletePageContent />
    </ProtectedRoute>
  );
}
