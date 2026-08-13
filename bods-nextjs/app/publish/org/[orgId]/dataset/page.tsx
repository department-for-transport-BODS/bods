'use client';

import { FormEvent, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS } from '@/config/client';

type DatasetType = 'timetable' | 'avl' | 'fares';

function SelectDatasetTypePageContent() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;
  const [selectedType, setSelectedType] = useState<DatasetType | ''>('');
  const [showError, setShowError] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedType) {
      setShowError(true);
      return;
    }

    let targetPath: string;
    if (selectedType === 'fares') {
      targetPath = `/publish/org/${orgId}/dataset/fares/create`;
    } else if (selectedType === 'avl') {
      targetPath = `/publish/org/${orgId}/dataset/avl/new`;
    } else {
      targetPath = `/publish/org/${orgId}/dataset/${selectedType}`;
    }

    router.push(targetPath);
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.data },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'Choose data type', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
            <ErrorSummary errors={showError ? ['Please select a data type'] : []} summaryId="dataset-type-error-title" />

            <form onSubmit={handleSubmit}>
              <div className={`govuk-form-group${showError ? ' govuk-form-group--error' : ''}`}>
                <fieldset className="govuk-fieldset" aria-describedby="dataset-type-hint">
                  <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <h1 className="govuk-fieldset__heading">Choose data type</h1>
                  </legend>
                  <div id="dataset-type-hint" className="govuk-hint">
                    Please choose the type of data you would like to publish.
                  </div>
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
  );
}

export default function SelectDatasetTypePage() {
  return (
    <ProtectedRoute>
      <SelectDatasetTypePageContent />
    </ProtectedRoute>
  );
}