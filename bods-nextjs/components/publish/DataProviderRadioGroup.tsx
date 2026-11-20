import { URL_LINK_ITEM_ID, UPLOAD_FILE_ITEM_ID } from './constants';

type DataProviderRadioGroupProps = {
  selectedMethod: 'link' | 'file' | typeof URL_LINK_ITEM_ID | typeof UPLOAD_FILE_ITEM_ID | '' | null;
  link: string;
  /** Rendered as the fieldset legend heading, like Django's `RadioAccordion(use_legend_as_heading=True)`. */
  legend?: string;
  fileAccept?: string;
  urlHint?: string;
  fileHint?: string;
  urlAriaLabel?: string;
  fileAriaLabel?: string;
  fileSelected?: boolean;
  errors?: { link?: string; file?: string; method?: string };
  onMethodChange: (method: 'link' | 'file') => void;
  onLinkChange: (value: string) => void;
  onFileChange: (file: File | null) => void;
};

function isLinkSelected(method: DataProviderRadioGroupProps['selectedMethod']): boolean {
  return method === 'link' || method === URL_LINK_ITEM_ID;
}

function isFileSelected(method: DataProviderRadioGroupProps['selectedMethod']): boolean {
  return method === 'file' || method === UPLOAD_FILE_ITEM_ID;
}

function formGroupClass(error?: string): string {
  return error ? 'govuk-form-group govuk-form-group--error' : 'govuk-form-group';
}

function conditionalClass(visible: boolean): string {
  return visible ? 'govuk-radios__conditional' : 'govuk-radios__conditional govuk-radios__conditional--hidden';
}

/**
 * Django's `RadioAccordion` for `FeedUploadForm`/`FaresFeedUploadForm`: both conditional inputs are
 * always rendered and hidden with `govuk-radios__conditional--hidden` until their radio is checked.
 */
export function DataProviderRadioGroup({
  selectedMethod,
  link,
  legend,
  fileAccept,
  urlHint,
  fileHint,
  urlAriaLabel,
  fileAriaLabel,
  fileSelected = false,
  errors,
  onMethodChange,
  onLinkChange,
  onFileChange,
}: DataProviderRadioGroupProps) {
  // Django's `clean()` adds the no-selection error to `url_link`, and `RadioAccordion` opens the
  // first group with errors, so the URL group is shown with the error on its input.
  const noSelectionError = selectedMethod ? undefined : errors?.method;
  const linkError = errors?.link ?? noSelectionError;
  const linkSelected = isLinkSelected(selectedMethod) || Boolean(noSelectionError);
  const fileChosen = isFileSelected(selectedMethod);

  return (
    <>
      <div className="govuk-form-group" data-module="app-radio-accordion">
        <fieldset className="govuk-fieldset">
          {legend && (
            <legend className="govuk-fieldset__legend govuk-fieldset__legend--m">
              <h1 className="govuk-heading-xl">{legend}</h1>
            </legend>
          )}
          <div className="govuk-radios govuk-radios--conditional" data-module="govuk-radios">
            <div className="govuk-radios__item">
              <input
                className="govuk-radios__input"
                id={`${URL_LINK_ITEM_ID}-radio`}
                name="selected_item"
                type="radio"
                value={URL_LINK_ITEM_ID}
                checked={linkSelected}
                onChange={() => onMethodChange('link')}
                data-aria-controls={URL_LINK_ITEM_ID}
              />
              <label className="govuk-label govuk-radios__label" htmlFor={`${URL_LINK_ITEM_ID}-radio`}>
                Provide a link to your data set
              </label>
            </div>
            <div id={URL_LINK_ITEM_ID} className={conditionalClass(linkSelected)}>
              <div className={formGroupClass(linkError)}>
                <label className="govuk-label" htmlFor="id_url_link">
                  URL Link
                </label>
                {urlHint && (
                  <span id="id_url_link-hint" className="govuk-hint">
                    {urlHint}
                  </span>
                )}
                {linkError && (
                  <span id="1_id_url_link-error" className="govuk-error-message">
                    {linkError}
                  </span>
                )}
                <input
                  type="url"
                  name="url_link"
                  maxLength={500}
                  className="govuk-!-width-three-quarters govuk-input"
                  aria-label={urlAriaLabel}
                  aria-describedby={urlHint ? 'id_url_link-hint' : undefined}
                  id="id_url_link"
                  value={link}
                  onChange={(e) => onLinkChange(e.target.value)}
                />
              </div>
            </div>
            <div className="govuk-radios__item">
              <input
                className="govuk-radios__input"
                id={`${UPLOAD_FILE_ITEM_ID}-radio`}
                name="selected_item"
                type="radio"
                value={UPLOAD_FILE_ITEM_ID}
                checked={fileChosen}
                onChange={() => onMethodChange('file')}
                data-aria-controls={UPLOAD_FILE_ITEM_ID}
              />
              <label className="govuk-label govuk-radios__label" htmlFor={`${UPLOAD_FILE_ITEM_ID}-radio`}>
                Upload data set to Bus Open Data Service
              </label>
            </div>
            <div id={UPLOAD_FILE_ITEM_ID} className={conditionalClass(fileChosen)}>
              <div className={formGroupClass(errors?.file)}>
                <label className="govuk-label" htmlFor="id_upload_file">
                  Upload File
                </label>
                {fileHint && (
                  <span id="id_upload_file-hint" className="govuk-hint">
                    {fileHint}
                  </span>
                )}
                {errors?.file && (
                  <span id="1_id_upload_file-error" className="govuk-error-message">
                    {errors.file}
                  </span>
                )}
                <input
                  type="file"
                  name="upload_file"
                  className="govuk-file-upload hidden-overflow"
                  aria-label={fileAriaLabel}
                  aria-describedby={fileHint ? 'id_upload_file-hint' : undefined}
                  id="id_upload_file"
                  accept={fileAccept}
                  onChange={(e) => onFileChange(e.target.files?.[0] || null)}
                />
              </div>
            </div>
          </div>
        </fieldset>
      </div>
      <span
        id="file-select-success"
        className="govuk-hint"
        style={fileChosen && fileSelected ? undefined : { display: 'none' }}
      >
        Your file has been selected
      </span>
    </>
  );
}
