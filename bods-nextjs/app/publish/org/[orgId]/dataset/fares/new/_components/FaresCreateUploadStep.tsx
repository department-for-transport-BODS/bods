'use client';

import { FormEvent } from 'react';
import {
  FARES_UPLOAD_FILE_ITEM_ID,
  FARES_URL_LINK_ITEM_ID,
  type FaresUploadErrors,
  type FaresUploadItem,
} from '@/lib/validation/fares-publish';
import { FormButtons } from './FormButtons';

function RadioItem({
  id,
  label,
  selectedItem,
  onSelect,
}: Readonly<{
  id: FaresUploadItem;
  label: string;
  selectedItem: FaresUploadItem | null;
  onSelect: (value: FaresUploadItem) => void;
}>) {
  return (
    <div className="govuk-radios__item">
      <input
        className="govuk-radios__input"
        id={`${id}-radio`}
        name="selected_item"
        type="radio"
        value={id}
        checked={selectedItem === id}
        aria-controls={id}
        onChange={() => onSelect(id)}
      />
      <label className="govuk-label govuk-radios__label" htmlFor={`${id}-radio`}>
        {label}
      </label>
    </div>
  );
}

function conditionalClass(id: FaresUploadItem, selectedItem: FaresUploadItem | null) {
  return `govuk-radios__conditional${selectedItem === id ? '' : ' govuk-radios__conditional--hidden'}`;
}

// Mirrors Django `FaresFeedUploadForm` (RadioAccordion) as rendered by `fares/feed_form.html`.
export function FaresCreateUploadStep({
  selectedItem,
  urlLink,
  errors,
  isSubmitting,
  onSelectedItemChange,
  onUrlLinkChange,
  onUploadFileChange,
  onSubmit,
  onCancel,
}: Readonly<{
  selectedItem: FaresUploadItem | null;
  urlLink: string;
  errors: FaresUploadErrors;
  isSubmitting: boolean;
  onSelectedItemChange: (value: FaresUploadItem) => void;
  onUrlLinkChange: (value: string) => void;
  onUploadFileChange: (file: File | null) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}>) {
  const hasErrors = Boolean(errors.urlLink || errors.uploadFile);

  return (
    <form method="post" encType="multipart/form-data" onSubmit={onSubmit} noValidate>
      <div className={`govuk-form-group${hasErrors ? ' govuk-form-group--error' : ''}`}>
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--m">
            <h1 className="govuk-heading-xl">Choose how to provide your data set</h1>
          </legend>
          <div className="govuk-radios govuk-radios--conditional">
            <RadioItem
              id={FARES_URL_LINK_ITEM_ID}
              label="Provide a link to your data set"
              selectedItem={selectedItem}
              onSelect={onSelectedItemChange}
            />
            <div id={FARES_URL_LINK_ITEM_ID} className={conditionalClass(FARES_URL_LINK_ITEM_ID, selectedItem)}>
              <div className="govuk-form-group">
                <label className="govuk-label" htmlFor="id_url_link">
                  URL Link
                </label>
                <span id="id_url_link-hint" className="govuk-hint">
                  Please provide a URL link where your NeTEX files are hosted. Example address:
                  &apos;mybuscompany.com/fares.xml&apos;.
                </span>
                {errors.urlLink ? (
                  <span id="1_id_url_link-error" className="govuk-error-message">
                    {errors.urlLink}
                  </span>
                ) : null}
                <input
                  type="url"
                  id="id_url_link"
                  name="url_link"
                  maxLength={500}
                  className={`govuk-!-width-three-quarters govuk-input${errors.urlLink ? ' govuk-input--error' : ''}`}
                  aria-label="url link"
                  aria-describedby="id_url_link-hint"
                  value={urlLink}
                  onChange={(event) => onUrlLinkChange(event.target.value)}
                />
              </div>
            </div>
            <RadioItem
              id={FARES_UPLOAD_FILE_ITEM_ID}
              label="Upload data set to Bus Open Data Service"
              selectedItem={selectedItem}
              onSelect={onSelectedItemChange}
            />
            <div id={FARES_UPLOAD_FILE_ITEM_ID} className={conditionalClass(FARES_UPLOAD_FILE_ITEM_ID, selectedItem)}>
              <div className="govuk-form-group">
                <label className="govuk-label" htmlFor="id_upload_file">
                  Upload File
                </label>
                <span id="id_upload_file-hint" className="govuk-hint">
                  This must be either NeTEX (see description in guidance) or a zip consisting only of NeTEX files
                </span>
                {errors.uploadFile ? (
                  <span id="1_id_upload_file-error" className="govuk-error-message">
                    {errors.uploadFile}
                  </span>
                ) : null}
                <input
                  type="file"
                  id="id_upload_file"
                  name="upload_file"
                  className={`govuk-file-upload hidden-overflow${errors.uploadFile ? ' govuk-file-upload--error' : ''}`}
                  aria-label="Choose file"
                  aria-describedby="id_upload_file-hint"
                  onChange={(event) => onUploadFileChange(event.target.files?.[0] ?? null)}
                />
              </div>
            </div>
          </div>
        </fieldset>
      </div>
      <span id="file-select-success" className="govuk-hint" style={{ display: 'none' }}>
        Your file has been selected
      </span>
      <FormButtons isSubmitting={isSubmitting} onCancel={onCancel} />
    </form>
  );
}
