'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  DataProviderRadioGroup,
  PublishCancelStep,
  PublishCommentStep,
  PublishStepper,
  type PublishStep,
  UPLOAD_FILE_ITEM_ID,
  URL_LINK_ITEM_ID,
} from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { publishAppPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { REQUIRED_COMMENT_ERROR } from '@/lib/validation/messages';
import { validateTimetableStep2 } from '@/lib/validation/timetable-publish';
import { TimetableHelpAside } from './TimetableHelpAside';

/**
 * - `update`: Django `FeedUpdateWizard` (`update/`), comment then upload, starting a new draft from the live data set.
 * - `publishModify`: Django `TimetableUploadModify` (`review/update/`), replacing the data of a first-publish draft.
 * - `updateModify`: Django `DatasetUpdateModify` (`update/review/update/`), replacing the data of an update draft.
 */
export type TimetableUpdateMode = 'update' | 'publishModify' | 'updateModify';

type Step = 'comment' | 'upload' | 'cancel';

const COMMENT_HINT =
  'Please add a comment to describe the updates you have made to this data set. Users will see this information in the change log.';

type TimetableUpdateContentProps = {
  mode: TimetableUpdateMode;
};

export function TimetableUpdateContent({ mode }: Readonly<TimetableUpdateContentProps>) {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const datasetUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}`;
  const isUpdateJourney = mode !== 'publishModify';
  const reviewUrl = isUpdateJourney ? `${datasetUrl}/update/review` : `${datasetUrl}/review`;
  const cancelConfirmUrl = {
    update: `${datasetUrl}/`,
    publishModify: `${datasetUrl}/review/`,
    updateModify: `${datasetUrl}/update/review/`,
  }[mode];

  const initialStep = mode === 'update' ? 'comment' : 'upload';
  const [step, setStep] = useState<Step>(initialStep);
  const [stepBeforeCancel, setStepBeforeCancel] = useState<Exclude<Step, 'cancel'>>(initialStep);
  const [comment, setComment] = useState('');
  const [commentError, setCommentError] = useState('');
  const [selectedMethod, setSelectedMethod] = useState<'link' | 'file' | ''>('');
  const [link, setLink] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const hasErrors = Boolean(commentError || submitError || Object.keys(errors).length > 0);
  useEffect(() => {
    const titlePrefix = isUpdateJourney ? 'Update data set' : 'Provide data';
    document.title = `${hasErrors && step !== 'cancel' ? 'Error: ' : ''}${titlePrefix}: ${step}`;
  }, [isUpdateJourney, step, hasErrors]);

  // Django binds the upload form to the revision it edits, pre-filling its URL link: the draft when
  // modifying, otherwise `start_revision()`, which copies the live revision's link.
  useEffect(() => {
    const url =
      mode === 'update'
        ? `/api/publish/timetables/update/${orgId}/${datasetId}/`
        : `/api/publish/timetables/review-status/${orgId}/${datasetId}/`;
    api
      .get<{ urlLink?: string | null }>(url)
      .then((data) => setLink((current) => current || data.urlLink || ''))
      .catch(() => undefined);
  }, [mode, orgId, datasetId]);

  const startCancel = (from: Exclude<Step, 'cancel'>) => {
    setStepBeforeCancel(from);
    setStep('cancel');
  };

  const handleCommentSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!comment.trim()) {
      setCommentError(REQUIRED_COMMENT_ERROR);
      return;
    }
    setCommentError('');
    setStep('upload');
  };

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
    if (mode === 'update') {
      formData.set('comment', comment);
    } else {
      formData.set('modify_draft', 'true');
    }
    if (mode === 'updateModify') formData.set('is_update', 'true');

    try {
      const response = await api.post<{ redirect?: string }>(
        `/api/publish/timetables/update/${orgId}/${datasetId}/`,
        formData,
      );
      router.push(response.redirect || reviewUrl);
    } catch (error) {
      setIsSubmitting(false);
      const commentFieldError = error instanceof ApiError ? error.firstFieldErrors().comment : undefined;
      if (commentFieldError) {
        // Django validates the comment on its own wizard step, so its errors render there.
        setCommentError(commentFieldError);
        setStep('comment');
        return;
      }
      setSubmitError(error instanceof Error ? error.message : 'Unable to update data set. Please try again.');
    }
  };

  if (step === 'cancel') {
    return (
      <PublishCancelStep
        heading="Would you like to cancel updating this data set?"
        confirmHref={publishAppPath(cancelConfirmUrl)}
        onBack={() => setStep(stepBeforeCancel)}
      />
    );
  }

  const summaryErrors = [
    errors.method ? { text: errors.method, href: '#id_url_link' } : null,
    errors.link ? { text: errors.link, href: '#id_url_link' } : null,
    errors.file ? { text: errors.file, href: '#id_upload_file' } : null,
  ].filter((error): error is { text: string; href: string } => error !== null);

  const stepperSteps: PublishStep[] = isUpdateJourney
    ? [
        { label: '1. Comment', state: step === 'comment' ? 'selected' : 'previous' },
        { label: '2. Update', state: step === 'upload' ? 'selected' : 'next' },
        { label: '3. Review and publish', state: 'next' },
      ]
    : [
        { label: '1. Describe data', state: 'previous' },
        { label: '2. Provide data', state: 'selected' },
        { label: '3. Review and publish', state: 'next' },
      ];

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <PublishStepper steps={stepperSteps} />
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {step === 'comment' ? (
              <PublishCommentStep
                comment={comment}
                hint={COMMENT_HINT}
                errorMessage={commentError}
                onChange={setComment}
                onSubmit={handleCommentSubmit}
                onCancel={() => startCancel('comment')}
              />
            ) : (
              <>
                <ErrorSummary errors={submitError ? [submitError] : summaryErrors} summaryId="timetable-update-error-title" />
                <DataProviderRadioGroup
                  legend={mode === 'update' ? 'Update your published data set' : 'Choose how to provide your data set'}
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
                  <button
                    type="button"
                    name="cancel"
                    value="cancel"
                    className="govuk-button govuk-button--secondary"
                    data-module="govuk-button"
                    onClick={() => startCancel('upload')}
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
          <TimetableHelpAside />
        </div>
      </div>
    </div>
  );
}
