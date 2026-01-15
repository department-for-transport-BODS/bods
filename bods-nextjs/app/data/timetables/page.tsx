/**
 * Timetables List Page
 * 
 * Browse and search timetable datasets
 */

'use client';

import { useState, useEffect } from 'react';
import { getPaginated } from '@/lib/api-client';
import Link from 'next/link';

interface TimetableDataset {
  id: number;
  name: string;
  description?: string;
  status: string;
  created: string;
  modified: string;
}

export default function TimetablesPage() {
  const [datasets, setDatasets] = useState<TimetableDataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setIsLoading(true);
      const data = await getPaginated<TimetableDataset>('/api/v1/dataset/', { requireAuth: false });
      setDatasets(data.results);
    } catch (err) {
      setError('Failed to load datasets');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Timetable datasets</h1>

        {error && (
          <div className="govuk-error-summary" role="alert">
            <h2 className="govuk-error-summary__title">Error</h2>
            <div className="govuk-error-summary__body">
              <p>{error}</p>
            </div>
          </div>
        )}

        {isLoading ? (
          <p className="govuk-body">Loading datasets...</p>
        ) : (
          <table className="govuk-table">
            <thead className="govuk-table__head">
              <tr className="govuk-table__row">
                <th className="govuk-table__header">Name</th>
                <th className="govuk-table__header">Status</th>
                <th className="govuk-table__header">Last modified</th>
                <th className="govuk-table__header">Actions</th>
              </tr>
            </thead>
            <tbody className="govuk-table__body">
              {datasets.map((dataset) => (
                <tr key={dataset.id} className="govuk-table__row">
                  <td className="govuk-table__cell">
                    <Link href={`/data/timetables/${dataset.id}`} className="govuk-link">
                      {dataset.name}
                    </Link>
                  </td>
                  <td className="govuk-table__cell">{dataset.status}</td>
                  <td className="govuk-table__cell">
                    {new Date(dataset.modified).toLocaleDateString()}
                  </td>
                  <td className="govuk-table__cell">
                    <Link href={`/data/timetables/${dataset.id}`} className="govuk-link">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

