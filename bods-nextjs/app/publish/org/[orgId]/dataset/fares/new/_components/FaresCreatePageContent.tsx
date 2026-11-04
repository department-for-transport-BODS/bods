'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { PublishStepper } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { publishAppPath, wwwPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';
import {
  FARES_URL_LINK_ITEM_ID,
  type FaresUploadErrors,
  type FaresUploadItem,
  validateFaresDescriptionStep,
  validateFaresUploadStep,
} from '@/lib/validation/fares-publish';
import { FaresCreateCancelStep } from './FaresCreateCancelStep';
import { FaresCreateDescriptionStep } from './FaresCreateDescriptionStep';
import { FaresCreateUploadStep } from './FaresCreateUploadStep';

type FormStep = 'description' | 'upload';
type Step = FormStep | 'cancel';
type DescriptionErrors = { description?: string; shortDescription?: string };

const ERROR_ANCHORS = {
  description: '#id_description-description',
  shortDescription: '#id_description-short_description',
  urlLink: '#id_url_link',
  uploadFile: '#id_upload_file',
};

export function FaresCreatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;

  const [step, setStep] = useState<Step>('description');
  const [stepBeforeCancel, setStepBeforeCancel] = useState<FormStep>('description');
  const [description, setDescription] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  // Django's wizard only stores a step's data once it validates, so cancelling discards edits.
  const [savedDescription, setSavedDescription] = useState({ description: '', shortDescription: '' });
  const [selectedItem, setSelectedItem] = useState<FaresUploadItem | null>(null);
  const [urlLink, setUrlLink] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [descriptionErrors, setDescriptionErrors] = useState<DescriptionErrors>({});
  const [uploadErrors, setUploadErrors] = useState<FaresUploadErrors>({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const summaryErrors =
    step === 'description'
      ? errorSummaryItems(descriptionErrors, ERROR_ANCHORS)
      : step === 'upload'
        ? errorSummaryItems({ ...uploadErrors, submitError }, ERROR_ANCHORS)
        : [];

  useEffect(() => {
    document.title = `${summaryErrors.length > 0 ? 'Error: ' : ''}Publish new data set: ${step}`;
  }, [step, summaryErrors.length]);

  useEffect(() => {
    if (summaryErrors.length > 0) {
      document.querySelector<HTMLElement>('.govuk-error-summary')?.focus();
    }
  }, [descriptionErrors, uploadErrors, submitError, summaryErrors.length]);

  const handleDescriptionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const errors = validateFaresDescriptionStep({ description, shortDescription });
    setDescriptionErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSavedDescription({ description, shortDescription });
    setStep('upload');
  };

  const handleCancel = (from: FormStep) => {
    setStepBeforeCancel(from);
    setStep('cancel');
  };

  const handleCancelBack = () => {
    if (stepBeforeCancel === 'description') {
      setDescription(savedDescription.description);
      setShortDescription(savedDescription.shortDescription);
      setDescriptionErrors({});
    } else {
      setSelectedItem(null);
      setUrlLink('');
      setUploadFile(null);
      setUploadErrors({});
      setSubmitError('');
    }
    setStep(stepBeforeCancel);
  };

  const handleUploadSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError('');
    const errors = validateFaresUploadStep({ selectedItem, urlLink, uploadFile });
    setUploadErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.set('description', description);
      formData.set('short_description', shortDescription);
      formData.set('selected_item', selectedItem ?? '');
      if (selectedItem === FARES_URL_LINK_ITEM_ID) {
        formData.set('url_link', urlLink);
      } else if (uploadFile) {
        formData.set('upload_file', uploadFile, uploadFile.name);
      }

      const data = await api.post<{ redirect?: string }>(`/api/publish/fares/create/${orgId}/`, formData);
      if (!data.redirect) {
        setSubmitError('Unexpected response from server.');
        setIsSubmitting(false);
        return;
      }

      globalThis.location.href = publishAppPath(data.redirect);
    } catch (error) {
      setIsSubmitting(false);
      if (error instanceof ApiError && error.hasFieldErrors) {
        const fieldErrors = error.firstFieldErrors();
        if (fieldErrors.description || fieldErrors.short_description) {
          setDescriptionErrors({
            description: fieldErrors.description,
            shortDescription: fieldErrors.short_description,
          });
          setStep('description');
          return;
        }
        if (fieldErrors.url_link || fieldErrors.upload_file) {
          setUploadErrors({ urlLink: fieldErrors.url_link, uploadFile: fieldErrors.upload_file });
          return;
        }
        setSubmitError(Object.values(fieldErrors)[0]);
        return;
      }
      setSubmitError(error instanceof Error ? error.message : 'An error occurred while submitting. Please try again.');
    }
  };

  if (step === 'cancel') {
    return (
      <div className="govuk-width-container">
        <FaresCreateCancelStep orgId={orgId} onBack={handleCancelBack} />
      </div>
    );
  }

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <div className="govuk-breadcrumbs">
            <PublishStepper
              steps={[
                { label: '1. Describe data', state: step === 'description' ? 'selected' : 'previous' },
                { label: '2. Provide data', state: step === 'upload' ? 'selected' : 'next' },
                { label: '3. Review and publish', state: 'next' },
              ]}
            />
          </div>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            <ErrorSummary errors={summaryErrors} tabIndex={-1} />
            {step === 'description' ? (
              <FaresCreateDescriptionStep
                description={description}
                shortDescription={shortDescription}
                errors={descriptionErrors}
                onDescriptionChange={setDescription}
                onShortDescriptionChange={setShortDescription}
                onSubmit={handleDescriptionSubmit}
                onCancel={() => handleCancel('description')}
              />
            ) : (
              <FaresCreateUploadStep
                selectedItem={selectedItem}
                urlLink={urlLink}
                errors={uploadErrors}
                isSubmitting={isSubmitting}
                onSelectedItemChange={setSelectedItem}
                onUrlLinkChange={setUrlLink}
                onUploadFileChange={setUploadFile}
                onSubmit={handleUploadSubmit}
                onCancel={() => handleCancel('upload')}
              />
            )}
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
