'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  DataProviderRadioGroup,
  PublishCancelStep,
  PublishStepper,
  UPLOAD_FILE_ITEM_ID,
  URL_LINK_ITEM_ID,
} from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { publishAppPath } from '@/config/client';
import { api } from '@/lib/api-client';
import { validateTimetableStep2 } from '@/lib/validation/timetable-publish';
import { TimetableHelpAside } from './TimetableHelpAside';

type TimetableUpdateContentProps = {
  /**
   * Django `DatasetUpdateModify` (`update/review/update`): modifies the draft of an update
   * revision. Returns to `update/review` and uses the Comment/Update stepper.
   */
  isUpdateReview?: boolean;
};

export function TimetableUpdateContent({ isUpdateReview = false }: Readonly<TimetableUpdateContentProps>) {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const datasetUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}`;
  const reviewUrl = isUpdateReview ? `${datasetUrl}/update/review` : `${datasetUrl}/review`;
  const [selectedMethod, setSelectedMethod] = useState<'link' | 'file' | ''>('');
  const [link, setLink] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  // Django's Cancel submit re-renders the same URL as the wizard's cancel step.
  const [isCancelling, setIsCancelling] = useState(false);

  useEffect(() => {
    document.title = `Update data set: ${isCancelling ? 'cancel' : 'upload'}`;
  }, [isCancelling]);

  const handleSubmit = async () => {
    const validationErrors = validateTimetableStep2({ selectedMethod, link, file });
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    setSubmitError('');
    const formData = new FormData();
    formData.set('selected_item', selectedMethod === 'link' ? URL_LINK_ITEM_ID : UPLOAD_FILE_ITEM_ID);
    if (selectedMethod === 'link') formData.set('url_link', link);
    if (selectedMethod === 'file' && file) formData.set('upload_file', file);
    if (isUpdateReview) formData.set('is_update', 'true');

    try {
      const response = await api.post<{ redirect?: string }>(
        `/api/publish/timetables/update/${orgId}/${datasetId}/`,
        formData,
      );
      router.push(response.redirect || reviewUrl);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Unable to update data set. Please try again.');
      setIsSubmitting(false);
    }
  };

  if (isCancelling) {
    return (
      <PublishCancelStep
        heading="Would you like to cancel updating this data set?"
        confirmHref={publishAppPath(`${datasetUrl}/update/review/`)}
        onBack={() => setIsCancelling(false)}
      />
    );
  }

  const summaryErrors = [
    errors.method ? { text: errors.method, href: `#${URL_LINK_ITEM_ID}-radio` } : null,
    errors.link ? { text: errors.link, href: '#id_url_link' } : null,
    errors.file ? { text: errors.file, href: '#id_upload_file' } : null,
  ].filter((error): error is { text: string; href: string } => error !== null);

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <PublishStepper
          steps={[
            { label: isUpdateReview ? '1. Comment' : '1. Describe data', state: 'previous' },
            { label: isUpdateReview ? '2. Update' : '2. Provide data', state: 'selected' },
            { label: '3. Review and publish', state: 'next' },
          ]}
        />
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            <ErrorSummary errors={submitError ? [submitError] : summaryErrors} summaryId="timetable-update-error-title" />
            <DataProviderRadioGroup
              legend={isUpdateReview ? 'Choose how to provide your data set' : 'Choose how to update your data'}
              selectedMethod={selectedMethod}
              link={link}
              fileAccept=".xml,.zip"
              urlHint="Please provide data set URL that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files."
              fileHint="Please provide data set file that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files"
              fileSelected={file !== null}
              errors={{ method: errors.method, link: errors.link, file: errors.file }}
              onMethodChange={setSelectedMethod}
              onLinkChange={setLink}
              onFileChange={setFile}
            />
            <div className="govuk-button-group govuk-!-margin-top-5">
              <button type="button" className="govuk-button" data-module="govuk-button" onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? 'Updating...' : 'Continue'}
              </button>
              {isUpdateReview ? (
                <button
                  type="button"
                  name="cancel"
                  value="cancel"
                  className="govuk-button govuk-button--secondary"
                  data-module="govuk-button"
                  onClick={() => setIsCancelling(true)}
                >
                  Cancel
                </button>
              ) : (
                <Link role="button" className="govuk-button govuk-button--secondary" href={`${datasetUrl}/update/cancel`}>
                  Cancel
                </Link>
              )}
            </div>
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
          <TimetableHelpAside />
        </div>
      </div>
    </div>
  );
}
