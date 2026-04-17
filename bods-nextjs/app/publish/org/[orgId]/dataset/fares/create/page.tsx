// implements the "Describe your data set" and "Choose how to provide your data set" steps of the fares dataset creation flow
// manages form state, handles form submissions to a custom API route, and includes a confirmation step for cancelling the process. 
// The page also displays error messages and links to support resources.
'use client';

import { FormEvent, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublishStepper, DatasetDescriptionFields, DataProviderRadioGroup, URL_LINK_ITEM_ID, UPLOAD_FILE_ITEM_ID } from '@/components/publish';

const DESCRIPTION_STEP = 'description';
const CANCEL_STEP = 'cancel';
const UPLOAD_STEP = 'upload';

function getHeadingText(step: typeof DESCRIPTION_STEP | typeof CANCEL_STEP | typeof UPLOAD_STEP) {
  if (step === CANCEL_STEP) {
    return 'Would you like to cancel publishing this data set?';
  }

  if (step === DESCRIPTION_STEP) {
    return 'Describe your data set';
  }

  return 'Choose how to provide your data set';
}

type FaresCreateStepContentProps = Readonly<{
  step: typeof DESCRIPTION_STEP | typeof CANCEL_STEP | typeof UPLOAD_STEP;
  description: string;
  shortDescription: string;
  selectedItem: typeof UPLOAD_FILE_ITEM_ID | typeof URL_LINK_ITEM_ID;
  urlLink: string;
  isSubmitting: boolean;
  onDescriptionSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onUploadSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDescriptionChange: (value: string) => void;
  onShortDescriptionChange: (value: string) => void;
  onSelectedItemChange: (value: typeof UPLOAD_FILE_ITEM_ID | typeof URL_LINK_ITEM_ID) => void;
  onUrlLinkChange: (value: string) => void;
  onUploadFileChange: (file: File | null) => void;
  onCancelClick: (step: typeof DESCRIPTION_STEP | typeof UPLOAD_STEP) => void;
  onCancelConfirm: () => void;
  onCancelBack: () => void;
}>;

function FaresCreateStepContent({
  step,
  description,
  shortDescription,
  selectedItem,
  urlLink,
  isSubmitting,
  onDescriptionSubmit,
  onUploadSubmit,
  onDescriptionChange,
  onShortDescriptionChange,
  onSelectedItemChange,
  onUrlLinkChange,
  onUploadFileChange,
  onCancelClick,
  onCancelConfirm,
  onCancelBack,
}: FaresCreateStepContentProps) {
  if (step === DESCRIPTION_STEP) {
    return (
      <form method="post" encType="multipart/form-data" onSubmit={onDescriptionSubmit} noValidate>
        <DatasetDescriptionFields
          description={description}
          shortDescription={shortDescription}
          descriptionHint="This information will give context to data set users. Please be descriptive but do not include personally identifiable information. You may wish to include: The original file name, start date of data, description of the fares, products, OpCo, locations/region, routes/service numbers for which the data applies, or any other useful high level information. The description should reflect the data included at a high level."
          shortDescriptionHint="This info will be displayed on your published data set dashboard to identify this data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 characters."
          onDescriptionChange={onDescriptionChange}
          onShortDescriptionChange={onShortDescriptionChange}
        />

        <div className="govuk-button-group">
          <button className="govuk-button" type="submit">
            Continue
          </button>
          <button className="govuk-button govuk-button--secondary" type="button" onClick={() => onCancelClick(DESCRIPTION_STEP)}>
            Cancel
          </button>
        </div>
      </form>
    );
  }

  if (step === CANCEL_STEP) {
    return (
      <div className="govuk-button-group">
        <button className="govuk-button app-!-mr-sm-4" type="button" onClick={onCancelConfirm}>
          Confirm
        </button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onCancelBack}>
          Cancel
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={onUploadSubmit} noValidate>
      <div className="govuk-form-group">
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-visually-hidden">Choose how to provide your data set</legend>
          <DataProviderRadioGroup
            selectedMethod={selectedItem}
            link={urlLink}
            urlHint="Please provide a URL link where your NeTEX files are hosted. Example address: mybuscompany.com/fares.xml."
            fileHint="This must be either NeTEX (see description in guidance) or a zip consisting only of NeTEX files"
            onMethodChange={(method) => onSelectedItemChange(method === 'link' ? URL_LINK_ITEM_ID : UPLOAD_FILE_ITEM_ID)}
            onLinkChange={onUrlLinkChange}
            onFileChange={onUploadFileChange}
          />
        </fieldset>
      </div>

      <div className="govuk-button-group">
        <button className="govuk-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Continue'}
        </button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={() => onCancelClick(UPLOAD_STEP)}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function FaresCreatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const djangoApiBaseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
  const djangoPublishBaseUrl =
    process.env.NEXT_PUBLIC_DJANGO_PUBLISH_URL || djangoApiBaseUrl.replace('://localhost', '://publish.localhost');
  const nextListUrl = `/publish/org/${orgId}/dataset/fares`;
  const supportBusOperatorsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/`;
  const contactSupportUrl = `${djangoApiBaseUrl}/contact/`;

  const [step, setStep] = useState<typeof DESCRIPTION_STEP | typeof CANCEL_STEP | typeof UPLOAD_STEP>(DESCRIPTION_STEP);
  const [stepBeforeCancel, setStepBeforeCancel] = useState<typeof DESCRIPTION_STEP | typeof UPLOAD_STEP>(DESCRIPTION_STEP);
  const [description, setDescription] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  const [selectedItem, setSelectedItem] = useState<typeof UPLOAD_FILE_ITEM_ID | typeof URL_LINK_ITEM_ID>(
    UPLOAD_FILE_ITEM_ID,
  );
  const [urlLink, setUrlLink] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const isCancelStep = step === CANCEL_STEP;
  const headingText = getHeadingText(step);

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

      const token = globalThis.window
        ? globalThis.window.localStorage.getItem('bods.auth.access')
        : null;

      const resp = await fetch(`/api/fares/create?orgId=${orgId}`, {
        method: 'POST',
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const data = (await resp.json().catch(() => ({}))) as { error?: string; redirect?: string };

      if (!resp.ok) {
        setErrorMessage(data.error || `Submit failed (${resp.status}).`);
        setIsSubmitting(false);
        return;
      }

      if (!data.redirect) {
        setErrorMessage('Unexpected response from server.');
        setIsSubmitting(false);
        return;
      }

      // Navigate within Next.js (the bridge rewrites Django URLs to Next.js paths)
      globalThis.location.href = data.redirect;
    } catch {
      setErrorMessage('An error occurred while submitting. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        {isCancelStep ? null : (
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
            <h1 className="govuk-heading-l">{headingText}</h1>

            {isCancelStep && (
              <p className="govuk-body">Any changes you have made so far will not be saved.</p>
            )}

            {errorMessage ? (
              <div className="govuk-error-summary" role="alert" aria-labelledby="fares-submit-error-title">
                <h2 className="govuk-error-summary__title" id="fares-submit-error-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    <li>{errorMessage}</li>
                  </ul>
                </div>
              </div>
            ) : null}

            <FaresCreateStepContent
              step={step}
              description={description}
              shortDescription={shortDescription}
              selectedItem={selectedItem}
              urlLink={urlLink}
              isSubmitting={isSubmitting}
              onDescriptionSubmit={handleDescriptionSubmit}
              onUploadSubmit={handleUploadSubmit}
              onDescriptionChange={setDescription}
              onShortDescriptionChange={setShortDescription}
              onSelectedItemChange={setSelectedItem}
              onUrlLinkChange={setUrlLink}
              onUploadFileChange={setUploadFile}
              onCancelClick={handleClickCancel}
              onCancelConfirm={handleCancelConfirm}
              onCancelBack={handleCancelBack}
            />

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
