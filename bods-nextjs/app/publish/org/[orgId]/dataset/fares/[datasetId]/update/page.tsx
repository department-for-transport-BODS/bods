'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const COMMENT_STEP = 'comment';
const UPLOAD_STEP = 'upload';
const CANCEL_STEP = 'cancel';
const UPLOAD_FILE_ITEM_ID = 'upload_file-conditional';
const URL_LINK_ITEM_ID = 'url_link-conditional';

type Step = typeof COMMENT_STEP | typeof UPLOAD_STEP | typeof CANCEL_STEP;
type UploadItem = typeof UPLOAD_FILE_ITEM_ID | typeof URL_LINK_ITEM_ID;

function CancelStepView({ onConfirm, onBack }: Readonly<{ onConfirm: () => void; onBack: () => void }>) {
  return (
    <>
      <h1 className="govuk-heading-l">Would you like to cancel updating this data set?</h1>
      <p className="govuk-body">Any changes you have made so far will not be saved.</p>
      <div className="govuk-button-group">
        <button className="govuk-button" type="button" onClick={onConfirm}>Confirm</button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onBack}>Cancel</button>
      </div>
    </>
  );
}

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
      {errorMessage ? (
        <div className="govuk-error-summary" role="alert" aria-labelledby="comment-error-title">
          <h2 className="govuk-error-summary__title" id="comment-error-title">There is a problem</h2>
          <div className="govuk-error-summary__body">
            <ul className="govuk-list govuk-error-summary__list"><li>{errorMessage}</li></ul>
          </div>
        </div>
      ) : null}
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="comment">Comment on data set updates</label>
        <div className="govuk-hint">
          Provide a comment to describe what has changed in this update. For example: update to fares for route 36.
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
  reviewUrl,
  onCancel,
}: Readonly<{
  orgId: string;
  datasetId: string;
  comment: string;
  reviewUrl: string;
  onCancel: () => void;
}>) {
  const [selectedItem, setSelectedItem] = useState<UploadItem | null>(null);
  const [urlLink, setUrlLink] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
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
      formData.set('comment', comment);
      formData.set('selected_item', selectedItem);
      if (selectedItem === URL_LINK_ITEM_ID) {
        formData.set('url_link', urlLink);
      } else if (uploadFile) {
        formData.set('upload_file', uploadFile, uploadFile.name);
      }

      const token = globalThis.window
        ? globalThis.window.localStorage.getItem('bods.auth.access')
        : null;

      const resp = await fetch(`/api/fares/update?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = (await resp.json().catch(() => ({}))) as { error?: string; redirect?: string };
      if (!resp.ok) {
        setErrorMessage(data.error || `Upload failed (${resp.status}).`);
        setIsSubmitting(false);
        return;
      }
      globalThis.location.href = data.redirect || reviewUrl;
    } catch {
      setErrorMessage('An error occurred while uploading. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <h1 className="govuk-heading-l">Choose how to provide your data set</h1>
      {errorMessage ? (
        <div className="govuk-error-summary" role="alert" aria-labelledby="upload-error-title">
          <h2 className="govuk-error-summary__title" id="upload-error-title">There is a problem</h2>
          <div className="govuk-error-summary__body">
            <ul className="govuk-list govuk-error-summary__list"><li>{errorMessage}</li></ul>
          </div>
        </div>
      ) : null}
      <div className="govuk-form-group">
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-visually-hidden">Choose how to provide your data set</legend>
          <div className="govuk-radios">
            <div className="govuk-radios__item">
              <input
                className="govuk-radios__input"
                id={URL_LINK_ITEM_ID}
                name="selected_item"
                type="radio"
                value={URL_LINK_ITEM_ID}
                checked={selectedItem === URL_LINK_ITEM_ID}
                onChange={() => setSelectedItem(URL_LINK_ITEM_ID)}
              />
              <label className="govuk-label govuk-radios__label" htmlFor={URL_LINK_ITEM_ID}>
                Provide a link to your data set
              </label>
            </div>
            <div className="govuk-radios__item">
              <input
                className="govuk-radios__input"
                id={UPLOAD_FILE_ITEM_ID}
                name="selected_item"
                type="radio"
                value={UPLOAD_FILE_ITEM_ID}
                checked={selectedItem === UPLOAD_FILE_ITEM_ID}
                onChange={() => setSelectedItem(UPLOAD_FILE_ITEM_ID)}
              />
              <label className="govuk-label govuk-radios__label" htmlFor={UPLOAD_FILE_ITEM_ID}>
                Upload data set to Bus Open Data Service
              </label>
            </div>
          </div>
        </fieldset>
      </div>

      {selectedItem === URL_LINK_ITEM_ID ? (
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="id_url_link">URL Link</label>
          <div className="govuk-hint">
            Please provide a URL link where your NeTEX files are hosted. Example address: mybuscompany.com/fares.xml.
          </div>
          <input
            id="id_url_link"
            name="url_link"
            className="govuk-input govuk-!-width-three-quarters"
            type="url"
            aria-label="url link"
            value={urlLink}
            onChange={(e) => setUrlLink(e.target.value)}
          />
        </div>
      ) : null}

      {selectedItem === UPLOAD_FILE_ITEM_ID ? (
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="id_upload_file">Upload File</label>
          <div className="govuk-hint">
            This must be either NeTEX (see description in guidance) or a zip consisting only of NeTEX files
          </div>
          <input
            id="id_upload_file"
            name="upload_file"
            className="govuk-file-upload"
            type="file"
            aria-label="Choose file"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
          />
        </div>
      ) : null}

      <div className="govuk-button-group">
        <button className="govuk-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Uploading...' : 'Continue'}
        </button>
        <button
          className="govuk-button govuk-button--secondary"
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function FaresUpdatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const reviewUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/review`;
  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;

  const [step, setStep] = useState<Step>(COMMENT_STEP);
  const [stepBeforeCancel, setStepBeforeCancel] = useState<typeof COMMENT_STEP | typeof UPLOAD_STEP>(COMMENT_STEP);
  const [comment, setComment] = useState('');
  const [commentError, setCommentError] = useState('');

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

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        {step === CANCEL_STEP ? null : (
          <div className="govuk-breadcrumbs">
            <ol className="publish-stepper govuk-breadcrumbs__list" aria-label="Progress">
              <li className={`publish-stepper__item ${step === COMMENT_STEP ? 'publish-stepper__item--selected' : 'publish-stepper__item--previous'}`}>
                1. Add comment
              </li>
              <li className={`publish-stepper__item ${step === UPLOAD_STEP ? 'publish-stepper__item--selected' : 'publish-stepper__item--next'}`}>
                2. Provide data
              </li>
              <li className="publish-stepper__item publish-stepper__item--next">3. Review and publish</li>
            </ol>
          </div>
        )}

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {step === CANCEL_STEP ? (
              <CancelStepView
                onConfirm={() => { globalThis.location.href = faresListUrl; }}
                onBack={() => setStep(stepBeforeCancel)}
              />
            ) : null}
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
                <Link className="govuk-link large-font" href="/publish/guide-me">
                  View our guidelines here
                </Link>
              </li>
              <li>
                <Link className="govuk-link large-font" href="/publish/account">
                  Contact support desk
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent />
    </ProtectedRoute>
  );
}
