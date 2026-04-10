/**
 * Choose data type page
 *
 * Entry page for selecting the type of data to publish.
 */

'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Radios } from 'kainossoftwareltd-govuk-react-kainos';
import { getPaginated } from '@/lib/api-client';

type DataType = 'timetable' | 'avl' | 'fares';

interface Organisation {
  id: number;
}

function PublishDashboard() {
  const router = useRouter();
  const [selectedDataType, setSelectedDataType] = useState<DataType | ''>('');
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setHasSubmitted(true);

    if (!selectedDataType) {
      return;
    }

    setIsSubmitting(true);

    try {
      const data = await getPaginated<Organisation>('/api/organisations/');

      if (data.results.length === 1) {
        router.push(`/publish/org/${data.results[0].id}/dataset/${selectedDataType}`);
        return;
      }

      router.push(`/publish/org?dataType=${selectedDataType}`);
    } catch {
      router.push(`/publish/org?dataType=${selectedDataType}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Choose data type</h1>
            <form onSubmit={handleSubmit} noValidate>
              <Radios
                name="dataset_type"
                legend={{
                  children: 'Please choose the type of data you would like to publish.',
                  className: 'govuk-fieldset__legend govuk-fieldset__legend--m',
                }}
                items={[
                  { value: 'timetable', children: 'Timetables' },
                  { value: 'avl', children: 'Automatic Vehicle Locations (AVL)' },
                  { value: 'fares', children: 'Fares' },
                ]}
                value={selectedDataType}
                onChange={(event) => setSelectedDataType(event.target.value as DataType)}
                errorMessage={
                  hasSubmitted && !selectedDataType ? 'Please select a data type' : undefined
                }
              />

              <button
                type="submit"
                className="govuk-button"
                data-module="govuk-button"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Loading...' : 'Continue'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PublishPage() {
  return (
    <ProtectedRoute>
      <PublishDashboard />
    </ProtectedRoute>
  );
}

