'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { PublishCancelStep, PublishStepper } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { publishAppPath, wwwPath } from '@/config/client';
import { DATA_SET_UPLOAD_ERRORS } from '@/lib/validation/messages';
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

function CommentStepView({
  comment,
  errorMessage,
  onChange,
  onSubmit,
  onCancel,
}: Readonly<{
  comment: string;
  errorMessage: string;
  onChange: (v: string) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}>) {
  return (
    <form onSubmit={onSubmit} noValidate>
      <h1 className="govuk-heading-l">Provide a comment on what has been updated</h1>
      <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="comment-error-title" />
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="comment">Comment on data set updates</label>
        <div className="govuk-hint">
          This information will give context to data set users. Please be descriptive but do not
          include personally identifiable information. You may wish to include: The original file
          name, start date of data, description of the fares, products, OpCo, locations/region,
          routes/service numbers for which the data applies, or any other useful high level
          information. The description should reflect the data included at a high level.
        </div>
        <textarea
          className="govuk-textarea govuk-!-width-three-quarters"
          id="comment"
          name="comment"
          rows={3}
          value={comment}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
      <div className="govuk-button-group">
        <button className="govuk-button" type="submit">Continue</button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

function UploadStepView({
  orgId,
  datasetId,
  comment,
  modifyDraft,
  prefillUrlLink,
  reviewUrl,
  onCancel,
}: Readonly<{
  orgId: string;
  datasetId: string;
  comment: string;
  modifyDraft: boolean;
  /** Django's `DatasetUpdateModify` binds the form to the draft revision, pre-filling its URL link. */
  prefillUrlLink: boolean;
  reviewUrl: string;
  onCancel: () => void;
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
      formData.set('comment', comment);
      formData.set('selected_item', selectedItem);
      if (modifyDraft) {
        formData.set('modify_draft', 'true');
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

type FaresUpdatePageContentProps = {
  /**
   * Django `fares.views.update.DatasetUpdateModify` (`update/review/update`): upload step only,
   * modifying the draft of an update revision. Cancel returns to `update/review`.
   */
  isUpdateReview?: boolean;
};

export function FaresUpdatePageContent({ isUpdateReview = false }: Readonly<FaresUpdatePageContentProps>) {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const modifyDraft = isUpdateReview || searchParams.get('modifyDraft') === 'true';

  const detailUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}`;
  // Django's FeedUpdateWizard and both modify views finish on `update/review`.
  const reviewUrl = `${detailUrl}/update/review`;
  let cancelUrl = detailUrl;
  if (isUpdateReview) {
    cancelUrl = reviewUrl;
  } else if (modifyDraft) {
    cancelUrl = `${detailUrl}/review`;
  }

  const [step, setStep] = useState<Step>(modifyDraft ? UPLOAD_STEP : COMMENT_STEP);
  const [stepBeforeCancel, setStepBeforeCancel] = useState<typeof COMMENT_STEP | typeof UPLOAD_STEP>(
    modifyDraft ? UPLOAD_STEP : COMMENT_STEP,
  );
  const [comment, setComment] = useState('');
  const [commentError, setCommentError] = useState('');

  useEffect(() => {
    if (isUpdateReview) {
      document.title = `Update data set: ${step}`;
    }
  }, [isUpdateReview, step]);

  const handleCommentSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCommentError('');
    if (!comment.trim()) {
      setCommentError('Enter a comment in the box below');
      return;
    }
    setStep(UPLOAD_STEP);
  };

  const handleCancelClick = (from: typeof COMMENT_STEP | typeof UPLOAD_STEP) => {
    setStepBeforeCancel(from);
    setStep(CANCEL_STEP);
  };

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
          <PublishStepper
            steps={[
              { label: '1. Comment', state: step === COMMENT_STEP ? 'selected' : 'previous' },
              { label: '2. Update', state: step === UPLOAD_STEP ? 'selected' : 'next' },
              { label: '3. Review and publish', state: 'next' },
            ]}
          />
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {step === COMMENT_STEP ? (
              <CommentStepView
                comment={comment}
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
                prefillUrlLink={isUpdateReview}
                reviewUrl={reviewUrl}
                onCancel={() => handleCancelClick(UPLOAD_STEP)}
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
