'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { PublishCancelStep, PublishCommentStep, PublishStepper, type PublishStep } from '@/components/publish';
import { ApiError, api } from '@/lib/api-client';
import { publishAppPath, wwwPath } from '@/config/client';
import { DATA_SET_UPLOAD_ERRORS, REQUIRED_COMMENT_ERROR } from '@/lib/validation/messages';
import {
  FaresUploadItem,
  FaresUploadStep,
  UPLOAD_FILE_ITEM_ID,
  URL_LINK_ITEM_ID,
} from './FaresUploadStep';

const COMMENT_STEP = 'comment';
const UPLOAD_STEP = 'upload';
const CANCEL_STEP = 'cancel';

type Step = typeof COMMENT_STEP | typeof UPLOAD_STEP | typeof CANCEL_STEP;

const COMMENT_HINT =
  'This information will give context to data set users. Please be descriptive but do not include personally identifiable information. You may wish to include: The original file name, start date of data, description of the fares, products, OpCo, locations/region, routes/service numbers for which the data applies, or any other useful high level information. The description should reflect the data included at a high level.';

function UploadStepView({
  orgId,
  datasetId,
  comment,
  modifyDraft,
  prefillUrlLink,
  reviewUrl,
  onCancel,
  onCommentError,
}: Readonly<{
  orgId: string;
  datasetId: string;
  comment: string;
  modifyDraft: boolean;
  /** Django's modify views bind the form to the draft revision, pre-filling its URL link. */
  prefillUrlLink: boolean;
  reviewUrl: string;
  onCancel: () => void;
  onCommentError: (message: string) => void;
}>) {
  const [selectedItem, setSelectedItem] = useState<FaresUploadItem | null>(null);
  const [urlLink, setUrlLink] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ method?: string; link?: string; file?: string }>({});

  useEffect(() => {
    if (!prefillUrlLink) return;
    api
      .get<{ urlLink?: string | null }>(`/api/publish/fares/review-status/${orgId}/${datasetId}/`)
      .then((data) => setUrlLink((current) => current || data.urlLink || ''))
      .catch(() => undefined);
  }, [prefillUrlLink, orgId, datasetId]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage('');
    setFieldErrors({});
    if (!selectedItem) {
      setFieldErrors({ method: DATA_SET_UPLOAD_ERRORS.noSelection });
      return;
    }
    if (selectedItem === URL_LINK_ITEM_ID && !urlLink.trim()) {
      setFieldErrors({ link: DATA_SET_UPLOAD_ERRORS.link });
      return;
    }
    if (selectedItem === UPLOAD_FILE_ITEM_ID && !uploadFile) {
      setFieldErrors({ file: DATA_SET_UPLOAD_ERRORS.fileMissing });
      return;
    }
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.set('selected_item', selectedItem);
      if (modifyDraft) {
        formData.set('modify_draft', 'true');
      } else {
        formData.set('comment', comment);
      }
      if (selectedItem === URL_LINK_ITEM_ID) {
        formData.set('url_link', urlLink);
      } else if (uploadFile) {
        formData.set('upload_file', uploadFile, uploadFile.name);
      }

      const data = await api.post<{ redirect?: string }>(
        `/api/publish/fares/update/${orgId}/${datasetId}/`,
        formData,
      );
      globalThis.location.href = data.redirect || reviewUrl;
    } catch (error) {
      const commentFieldError = error instanceof ApiError ? error.firstFieldErrors().comment : undefined;
      if (commentFieldError) {
        // Django validates the comment on its own wizard step, so its errors render there.
        onCommentError(commentFieldError);
        return;
      }
      setErrorMessage(error instanceof Error ? error.message : 'An error occurred while uploading. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <FaresUploadStep
      selectedItem={selectedItem}
      urlLink={urlLink}
      isSubmitting={isSubmitting}
      errorMessage={errorMessage}
      fieldErrors={fieldErrors}
      heading={modifyDraft ? 'Choose how to provide your data set' : 'Update your published data set'}
      submitButtonText="Continue"
      errorTitleId="upload-error-title"
      disableCancel={isSubmitting}
      onSelectedItemChange={setSelectedItem}
      onUrlLinkChange={setUrlLink}
      onUploadFileChange={setUploadFile}
      onSubmit={handleSubmit}
      onCancel={onCancel}
    />
  );
}

/**
 * - `update`: Django `fares.views.update.FeedUpdateWizard` (`update/`), comment then upload, starting a new draft
 *   from the live data set.
 * - `publishModify`: Django `FaresDatasetUploadModify` (`review/update/`), replacing the data of a first-publish draft.
 * - `updateModify`: Django `fares.views.update.DatasetUpdateModify` (`update/review/update/`), replacing the data of
 *   an update draft.
 */
export type FaresUpdateMode = 'update' | 'publishModify' | 'updateModify';

export function FaresUpdatePageContent({ mode }: Readonly<{ mode: FaresUpdateMode }>) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const modifyDraft = mode !== 'update';
  const isUpdateJourney = mode !== 'publishModify';

  const detailUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}`;
  // Django's FeedUpdateWizard and both modify views finish on `update/review`.
  const reviewUrl = `${detailUrl}/update/review`;
  const cancelUrl = {
    update: detailUrl,
    publishModify: `${detailUrl}/review`,
    updateModify: reviewUrl,
  }[mode];

  const initialStep = modifyDraft ? UPLOAD_STEP : COMMENT_STEP;
  const [step, setStep] = useState<Step>(initialStep);
  const [stepBeforeCancel, setStepBeforeCancel] = useState<typeof COMMENT_STEP | typeof UPLOAD_STEP>(initialStep);
  const [comment, setComment] = useState('');
  const [commentError, setCommentError] = useState('');

  useEffect(() => {
    const titlePrefix = isUpdateJourney ? 'Update data set' : 'Provide data';
    document.title = `${commentError && step === COMMENT_STEP ? 'Error: ' : ''}${titlePrefix}: ${step}`;
  }, [isUpdateJourney, step, commentError]);

  const handleCommentSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!comment.trim()) {
      setCommentError(REQUIRED_COMMENT_ERROR);
      return;
    }
    setCommentError('');
    setStep(UPLOAD_STEP);
  };

  const handleServerCommentError = (message: string) => {
    setCommentError(message);
    setStep(COMMENT_STEP);
  };

  const handleCancelClick = (from: typeof COMMENT_STEP | typeof UPLOAD_STEP) => {
    setStepBeforeCancel(from);
    setStep(CANCEL_STEP);
  };

  const stepperSteps: PublishStep[] = isUpdateJourney
    ? [
        { label: '1. Comment', state: step === COMMENT_STEP ? 'selected' : 'previous' },
        { label: '2. Update', state: step === UPLOAD_STEP ? 'selected' : 'next' },
        { label: '3. Review and publish', state: 'next' },
      ]
    : [
        { label: '1. Describe data', state: 'previous' },
        { label: '2. Provide data', state: 'selected' },
        { label: '3. Review and publish', state: 'next' },
      ];

  if (step === CANCEL_STEP) {
    return (
      <PublishCancelStep
        heading="Would you like to cancel updating this data set?"
        confirmHref={publishAppPath(`${cancelUrl}/`)}
        onBack={() => setStep(stepBeforeCancel)}
      />
    );
  }

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <PublishStepper steps={stepperSteps} />
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {step === COMMENT_STEP ? (
              <PublishCommentStep
                comment={comment}
                hint={COMMENT_HINT}
                errorMessage={commentError}
                onChange={setComment}
                onSubmit={handleCommentSubmit}
                onCancel={() => handleCancelClick(COMMENT_STEP)}
              />
            ) : null}
            {step === UPLOAD_STEP ? (
              <UploadStepView
                orgId={orgId}
                datasetId={datasetId}
                comment={comment}
                modifyDraft={modifyDraft}
                prefillUrlLink={modifyDraft}
                reviewUrl={reviewUrl}
                onCancel={() => handleCancelClick(UPLOAD_STEP)}
                onCommentError={handleServerCommentError}
              />
            ) : null}
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a className="govuk-link large-font" href={publishAppPath('/guidance/operator-requirements')}>
                  View our guidelines here
                </a>
              </li>
              <li>
                <a className="govuk-link large-font" href={wwwPath('/contact')}>
                  Contact support desk
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
