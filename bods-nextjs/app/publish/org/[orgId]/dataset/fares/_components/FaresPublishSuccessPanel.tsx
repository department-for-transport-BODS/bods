'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect } from 'react';
import { ErrorDisplay, LoadingSpinner } from '@/components/shared';
import { useApiResource } from '@/hooks/useApiResource';
import { api } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';

type FaresUpdateSuccessData = {
  isFaresValidatorActive: boolean;
  validatorError: boolean;
};

/**
 * Shared "Data set published" / "Data set updated" panel
 * (Django `fares/revision_publish_success.html`).
 */
export function FaresPublishSuccessPanel({ update = false }: Readonly<{ update?: boolean }>) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const faresListUrl = publishAppPath(`/publish/org/${orgId}/dataset/fares`);
  const datasetDetailUrl = publishAppPath(`/publish/org/${orgId}/dataset/fares/${datasetId}`);
  useEffect(() => {
    document.title = update ? 'Data set updated' : 'Data set published';
  }, [update]);

  // Django's publish and update success views both read the published revision's fares validation
  // result, shown when the fares validator flag is on.
  const fetchContext = useCallback(
    () => api.get<FaresUpdateSuccessData>(`/api/publish/fares/update-success/${orgId}/${datasetId}/`),
    [orgId, datasetId],
  );
  const { data, isLoading, error } = useApiResource(fetchContext, 'Failed to load data set');

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorDisplay type="generic" message={error} />;
  }

  const showValidatorError = Boolean(data?.isFaresValidatorActive && data.validatorError);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <hr className="govuk-section-break govuk-section-break--m govuk-section-break" />
            <div className="govuk-panel--confirmation govuk-panel">
              <h1 className="govuk-panel__title">
                Your data set has been successfully {update ? 'updated' : 'published'}
              </h1>
            </div>

            <p className="govuk-body-m">
              We have sent you a confirmation email.
            </p>

            {showValidatorError ? (
              <p className="govuk-body-m">
                Your dataset failed the validation set and will be marked as not compliant. Please contact your
                supplier to create a compliant dataset.
              </p>
            ) : null}

            <h2 className="govuk-heading-m">What happens next?</h2>
            <p className="govuk-body-m">
              You can view the data set on{' '}
              <Link className="govuk-link" href={faresListUrl}>
                your fares data sets
              </Link>{' '}
              or by clicking the button below. The data will now be live for everyone else to see.
            </p>

            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />

            <Link role="button" className="govuk-button" href={datasetDetailUrl}>
              View published data set
            </Link>

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
          <div className="govuk-!-width-one-third"></div>
        </div>
      </div>
    </div>
  );
}
