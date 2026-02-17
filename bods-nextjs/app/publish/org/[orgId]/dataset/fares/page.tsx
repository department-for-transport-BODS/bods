/**
 * Fares Publishing Page
 * 
 * Upload and manage fares datasets
 */

'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api-client';
import { useParams, useRouter } from 'next/navigation';

function FaresPublish() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      await api.post(`/api/org/${orgId}/dataset/fares/upload/`, formData);
      router.push(`/publish/org/${orgId}/dataset/fares/success`);
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Upload fares data</h1>

            {error && (
              <div className="govuk-error-summary" role="alert">
                <h2 className="govuk-error-summary__title">Error</h2>
                <p>{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="govuk-form-group">
                <label className="govuk-label" htmlFor="file">
                  Select fares file
                </label>
                <input
                  className="govuk-file-upload"
                  id="file"
                  name="file"
                  type="file"
                  accept=".xml,.zip"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  required
                />
              </div>

              <button
                type="submit"
                className="govuk-button"
                data-module="govuk-button"
                disabled={isUploading || !file}
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresPublishPage() {
  return (
    <ProtectedRoute>
      <FaresPublish />
    </ProtectedRoute>
  );
}

