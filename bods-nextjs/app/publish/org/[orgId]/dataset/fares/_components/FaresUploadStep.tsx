'use client';

import { FormEvent } from 'react';
import { ErrorSummary } from '@/components/shared';

export const UPLOAD_FILE_ITEM_ID = 'upload_file-conditional';
export const URL_LINK_ITEM_ID = 'url_link-conditional';

export type FaresUploadItem = typeof UPLOAD_FILE_ITEM_ID | typeof URL_LINK_ITEM_ID;

type FaresUploadStepProps = Readonly<{
  selectedItem: FaresUploadItem | null;
  urlLink: string;
  isSubmitting: boolean;
  errorMessage: string;
  heading: string;
  submitButtonText: string;
  errorTitleId: string;
  urlLinkHint?: string;
  disableCancel?: boolean;
  onSelectedItemChange: (value: FaresUploadItem) => void;
  onUrlLinkChange: (value: string) => void;
  onUploadFileChange: (file: File | null) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}>;

export function FaresUploadStep({
  selectedItem,
  urlLink,
  isSubmitting,
  errorMessage,
  heading,
  submitButtonText,
  errorTitleId,
  urlLinkHint = 'Please provide a URL link where your NeTEx files are hosted. Example address: mybuscompany.com/fares.xml.',
  disableCancel = false,
  onSelectedItemChange,
  onUrlLinkChange,
  onUploadFileChange,
  onSubmit,
  onCancel,
}: FaresUploadStepProps) {
  return (
    <form onSubmit={onSubmit} noValidate>
      <h1 className="govuk-heading-l">{heading}</h1>
      <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId={errorTitleId} />
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
                onChange={() => onSelectedItemChange(URL_LINK_ITEM_ID)}
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
                onChange={() => onSelectedItemChange(UPLOAD_FILE_ITEM_ID)}
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
          <label className="govuk-label" htmlFor="id_url_link">
            URL Link
          </label>
          <div className="govuk-hint">{urlLinkHint}</div>
          <input
            id="id_url_link"
            name="url_link"
            className="govuk-input govuk-!-width-three-quarters"
            type="url"
            aria-label="url link"
            value={urlLink}
            onChange={(event) => onUrlLinkChange(event.target.value)}
          />
        </div>
      ) : null}

      {selectedItem === UPLOAD_FILE_ITEM_ID ? (
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="id_upload_file">
            Upload File
          </label>
          <div className="govuk-hint">
            This must be either NeTEx (see description in guidance) or a zip consisting only of NeTEx files
          </div>
          <input
            id="id_upload_file"
            name="upload_file"
            className="govuk-file-upload"
            type="file"
            aria-label="Choose file"
            onChange={(event) => onUploadFileChange(event.target.files?.[0] || null)}
          />
        </div>
      ) : null}

      <div className="govuk-button-group">
        <button className="govuk-button" type="submit" disabled={isSubmitting}>
          {submitButtonText}
        </button>
        <button
          className="govuk-button govuk-button--secondary"
          type="button"
          onClick={onCancel}
          disabled={disableCancel}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}