'use client';

import { FormEvent, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS, publishAppPath } from '@/config/client';
import { useAuth } from '@/hooks/useAuth';

type DatasetType = 'timetable' | 'avl' | 'fares';

function SelectDatasetTypePageContent() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const orgId = params.orgId as string;
  const [selectedType, setSelectedType] = useState<DatasetType | ''>('');
  const [showError, setShowError] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedType) {
      setShowError(true);
      return;
    }

    router.push(`/publish/org/${orgId}/dataset/${selectedType}/new`);
  };

  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            ...(user?.is_agent_user
              ? [{ label: 'Operator Dashboard', href: publishAppPath('/org') }]
              : []),
            {
              label: 'Publish a Dataset or Data Feed',
              href: publishAppPath(`/org/${orgId}/dataset`),
              current: true,
            },
          ]}
        />
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
            <ErrorSummary errors={showError ? ['Please select a data type'] : []} summaryId="dataset-type-error-title" />

            <form onSubmit={handleSubmit}>
              <div className={`govuk-form-group${showError ? ' govuk-form-group--error' : ''}`}>
                <fieldset className="govuk-fieldset" aria-describedby="dataset-type-hint">
                  <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <h1 className="govuk-fieldset__heading">Choose data type</h1>
                  </legend>
                  <p id="dataset-type-hint" className="govuk-body govuk-!-font-weight-bold">
                    Please choose the type of data you would like to publish.
                  </p>
                  {showError ? (
                    <p id="dataset-type-error" className="govuk-error-message">
                      <span className="govuk-visually-hidden">Error:</span> Please select a data type
                    </p>
                  ) : null}

                  <div className="govuk-radios" data-module="govuk-radios">
                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="dataset-type-timetable"
                        name="dataset_type"
                        type="radio"
                        value="timetable"
                        checked={selectedType === 'timetable'}
                        onChange={() => {
                          setSelectedType('timetable');
                          setShowError(false);
                        }}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="dataset-type-timetable">
                        Timetables
                      </label>
                    </div>

                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="dataset-type-avl"
                        name="dataset_type"
                        type="radio"
                        value="avl"
                        checked={selectedType === 'avl'}
                        onChange={() => {
                          setSelectedType('avl');
                          setShowError(false);
                        }}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="dataset-type-avl">
                        Automatic Vehicle Locations (AVL)
                      </label>
                    </div>

                    <div className="govuk-radios__item">
                      <input
                        className="govuk-radios__input"
                        id="dataset-type-fares"
                        name="dataset_type"
                        type="radio"
                        value="fares"
                        checked={selectedType === 'fares'}
                        onChange={() => {
                          setSelectedType('fares');
                          setShowError(false);
                        }}
                      />
                      <label className="govuk-label govuk-radios__label" htmlFor="dataset-type-fares">
                        Fares
                      </label>
                    </div>
                  </div>
                </fieldset>
              </div>

              <button type="submit" className="govuk-button app-button--green" data-module="govuk-button">
                Continue
              </button>
            </form>
          </div>
        </div>
      </div>
      </div>
    </>
  );
}

export default function SelectDatasetTypePage() {
  return (
    <ProtectedRoute>
      <SelectDatasetTypePageContent />
    </ProtectedRoute>
  );
}