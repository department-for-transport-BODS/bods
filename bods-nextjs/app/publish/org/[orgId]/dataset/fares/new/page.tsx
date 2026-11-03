// Create flow keeps form state in-page and waits for processing before opening review.
'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublishStepper } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { useDatasetReview } from '@/hooks/useDatasetReview';
import { api } from '@/lib/api-client';
import {
  FaresUploadItem,
  FaresUploadStep,
  UPLOAD_FILE_ITEM_ID,
  URL_LINK_ITEM_ID,
} from '../_components/FaresUploadStep';

const DESCRIPTION_STEP = 'description';
const CANCEL_STEP = 'cancel';
const UPLOAD_STEP = 'upload';

type Step = typeof DESCRIPTION_STEP | typeof CANCEL_STEP | typeof UPLOAD_STEP;

type FaresProcessingStatus = {
  loading: boolean;
  progress: number;
};

function getDatasetIdFromReviewRedirect(redirect: string, orgId: string): string | null {
  const prefix = `/publish/org/${orgId}/dataset/fares/`;
  if (!redirect.startsWith(prefix)) {
    return null;
  }

  return redirect.slice(prefix.length).match(/^(\d+)\/review\/?$/)?.[1] ?? null;
}

function CancelStepView({ onConfirm, onBack }: Readonly<{ onConfirm: () => void; onBack: () => void }>) {
  return (
    <>
      <h1 className="govuk-heading-l">Would you like to cancel publishing this data set?</h1>
      <p className="govuk-body">Any changes you have made so far will not be saved.</p>
      <div className="govuk-button-group">
        <button className="govuk-button app-!-mr-sm-4" type="button" onClick={onConfirm}>
          Confirm
        </button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onBack}>
          Cancel
        </button>
      </div>
    </>
  );
}

function DescriptionStepView({
  description,
  shortDescription,
  errorMessage,
  onDescriptionChange,
  onShortDescriptionChange,
  onSubmit,
  onCancel,
}: Readonly<{
  description: string;
  shortDescription: string;
  errorMessage: string;
  onDescriptionChange: (value: string) => void;
  onShortDescriptionChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}>) {
  return (
    <form method="post" encType="multipart/form-data" onSubmit={onSubmit} noValidate>
      <h1 className="govuk-heading-l">Describe your data set</h1>
      <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="fares-description-error-title" />
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="id_description-description">
          Data set description
        </label>
        <div className="govuk-hint">
          This information will give context to data set users. Please be descriptive but do not include
          personally identifiable information. You may wish to include: The original file name, start date
          of data, description of the fares, products, OpCo, locations/region, routes/service numbers for
          which the data applies, or any other useful high level information. The description should reflect
          the data included at a high level.
        </div>
        <textarea
          id="id_description-description"
          name="description-description"
          className="govuk-textarea govuk-!-width-three-quarters"
          rows={3}
          value={description}
          onChange={(event) => onDescriptionChange(event.target.value)}
        />
      </div>
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="id_description-short_description">
          Data set short description
        </label>
        <div className="govuk-hint">
          This info will be displayed on your published data set dashboard to identify this data set and will
          not be visible to data set users. The maximum number of characters (with spaces) is 30 characters.
        </div>
        <input
          id="id_description-short_description"
          name="description-short_description"
          className="govuk-input govuk-!-width-three-quarters"
          maxLength={30}
          value={shortDescription}
          onChange={(event) => onShortDescriptionChange(event.target.value)}
        />
      </div>
      <div className="govuk-button-group">
        <button className="govuk-button" type="submit">
          Continue
        </button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function FaresCreatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const nextListUrl = `/publish/org/${orgId}/dataset/fares`;
  const supportBusOperatorsUrl = '/publish/guide-me';
  const contactSupportUrl = '/account';

  const [step, setStep] = useState<Step>(DESCRIPTION_STEP);
  const [stepBeforeCancel, setStepBeforeCancel] = useState<typeof DESCRIPTION_STEP | typeof UPLOAD_STEP>(DESCRIPTION_STEP);
  const [description, setDescription] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  const [selectedItem, setSelectedItem] = useState<FaresUploadItem | null>(null);
  const [urlLink, setUrlLink] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [processingDataset, setProcessingDataset] = useState<{
    datasetId: string;
    reviewUrl: string;
  } | null>(null);
  const {
    statusData: processingStatus,
    progress,
    errorMessage: processingError,
  } = useDatasetReview<FaresProcessingStatus>(
    processingDataset?.datasetId ?? '',
    processingDataset
      ? `/api/publish/fares/review-status/${orgId}/${processingDataset.datasetId}/`
      : '',
    'Unable to check processing status. Please refresh and try again.',
    '',
    { enabled: processingDataset !== null },
  );

  useEffect(() => {
    if (processingDataset && processingStatus && !processingStatus.loading) {
      globalThis.location.href = processingDataset.reviewUrl;
    }
  }, [processingDataset, processingStatus]);

  const handleDescriptionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage('');

    if (!description.trim() || !shortDescription.trim()) {
      setErrorMessage('Enter a data set description and short description.');
      return;
    }

    setStep(UPLOAD_STEP);
  };

  const handleClickCancel = (from: typeof DESCRIPTION_STEP | typeof UPLOAD_STEP) => {
    setStepBeforeCancel(from);
    setStep(CANCEL_STEP);
  };

  const handleCancelConfirm = () => {
    globalThis.location.href = nextListUrl;
  };

  const handleCancelBack = () => {
    setStep(stepBeforeCancel);
  };

  const handleUploadSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage('');

    if (!selectedItem) {
      setErrorMessage('Select how to provide your data set.');
      return;
    }

    if (selectedItem === URL_LINK_ITEM_ID && !urlLink.trim()) {
      setErrorMessage('Enter a URL link for your fares data.');
      return;
    }

    if (selectedItem === UPLOAD_FILE_ITEM_ID && !uploadFile) {
      setErrorMessage('Choose a fares file to upload.');
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.set('description', description);
      formData.set('short_description', shortDescription);
      formData.set('selected_item', selectedItem);

      if (selectedItem === URL_LINK_ITEM_ID) {
        formData.set('url_link', urlLink);
      } else if (uploadFile) {
        formData.set('upload_file', uploadFile, uploadFile.name);
      }

      const data = await api.post<{ redirect?: string }>(`/api/publish/fares/create/${orgId}/`, formData);

      const datasetId = data.redirect ? getDatasetIdFromReviewRedirect(data.redirect, orgId) : null;
      if (!data.redirect || !datasetId) {
        setErrorMessage('Unexpected response from server.');
        setIsSubmitting(false);
        return;
      }

      setProcessingDataset({ datasetId, reviewUrl: data.redirect });
      setIsSubmitting(false);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'An error occurred while submitting. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        {step === CANCEL_STEP ? null : (
          <div className="govuk-breadcrumbs">
            <div className="govuk-breadcrumbs">
              <PublishStepper
                steps={[
                  { label: '1. Describe data', state: step === DESCRIPTION_STEP ? 'selected' : 'previous' },
                  { label: '2. Provide data', state: step === UPLOAD_STEP ? 'selected' : 'next' },
                  { label: '3. Review and publish', state: 'next' },
                ]}
              />
            </div>
          </div>
          )}

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {step === CANCEL_STEP ? (
              <CancelStepView onConfirm={handleCancelConfirm} onBack={handleCancelBack} />
            ) : null}
            {step === DESCRIPTION_STEP ? (
              <DescriptionStepView
                description={description}
                shortDescription={shortDescription}
                errorMessage={errorMessage}
                onDescriptionChange={setDescription}
                onShortDescriptionChange={setShortDescription}
                onSubmit={handleDescriptionSubmit}
                onCancel={() => handleClickCancel(DESCRIPTION_STEP)}
              />
            ) : null}
            {step === UPLOAD_STEP ? (
              processingDataset ? (
                <>
                  <ErrorSummary errors={processingError ? [processingError] : []} summaryId="fares-processing-error-title" />
                  <div className="govuk-panel govuk-panel--confirmation">
                    <h2 className="govuk-panel__title govuk-!-font-size-36">Your data is being processed</h2>
                    <div className="govuk-panel__body govuk-!-font-size-19">
                      <div className="pb3-l">
                        The data format is being checked to confirm it is NeTEx.
                        <br />
                        Once successfully validated the data set details will
                        <br />
                        be shown here.
                      </div>
                      <div id="progressOuterDiv" className="progress-bar-outer">
                        <div
                          className="loading-white"
                          id="progressInnerDiv"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <span className="loading-white-lg" id="progressSpan">
                        {progress}%
                      </span>
                    </div>
                  </div>
                </>
              ) : (
                <FaresUploadStep
                  selectedItem={selectedItem}
                  urlLink={urlLink}
                  isSubmitting={isSubmitting}
                  errorMessage={errorMessage}
                  heading="Choose how to provide your data set"
                  submitButtonText={isSubmitting ? 'Submitting...' : 'Continue'}
                  errorTitleId="fares-upload-error-title"
                  onSelectedItemChange={setSelectedItem}
                  onUrlLinkChange={setUrlLink}
                  onUploadFileChange={setUploadFile}
                  onSubmit={handleUploadSubmit}
                  onCancel={() => handleClickCancel(UPLOAD_STEP)}
                />
              )
            ) : null}
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a className="govuk-link large-font" href={supportBusOperatorsUrl}>
                  View our guidelines here
                </a>
              </li>
              <li>
                <a className="govuk-link large-font" href={contactSupportUrl}>
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

export default function FaresCreatePage() {
  return (
    <ProtectedRoute>
      <FaresCreatePageContent />
    </ProtectedRoute>
  );
}
