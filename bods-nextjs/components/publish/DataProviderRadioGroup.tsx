import { URL_LINK_ITEM_ID, UPLOAD_FILE_ITEM_ID } from './constants';

type DataProviderRadioGroupProps = {
  selectedMethod: 'link' | 'file' | typeof URL_LINK_ITEM_ID | typeof UPLOAD_FILE_ITEM_ID | '';
  link: string;
  fileAccept?: string;
  urlHint?: string;
  fileHint?: string;
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

export function DataProviderRadioGroup({
  selectedMethod,
  link,
  fileAccept = '.xml,.zip',
  urlHint,
  fileHint,
  errors,
  onMethodChange,
  onLinkChange,
  onFileChange,
}: DataProviderRadioGroupProps) {
  return (
    <>
      {errors?.method && <p className="govuk-error-message">{errors.method}</p>}
      <div className="govuk-radios" data-module="govuk-radios">
        <div className="govuk-radios__item">
          <input
            className="govuk-radios__input"
            id="method-link"
            type="radio"
            name="method"
            checked={isLinkSelected(selectedMethod)}
            onChange={() => onMethodChange('link')}
          />
          <label className="govuk-label govuk-radios__label" htmlFor="method-link">
            Provide a link to your data set
          </label>
        </div>
        {isLinkSelected(selectedMethod) && (
          <div className="govuk-form-group">
            <label className="govuk-label" htmlFor="id_url_link">
              URL link
            </label>
            {urlHint && <div className="govuk-hint">{urlHint}</div>}
            {errors?.link && <p className="govuk-error-message">{errors.link}</p>}
            <input
              className="govuk-input"
              id="id_url_link"
              type="url"
              value={link}
              onChange={(e) => onLinkChange(e.target.value)}
            />
          </div>
        )}
        <div className="govuk-radios__item">
          <input
            className="govuk-radios__input"
            id="method-file"
            type="radio"
            name="method"
            checked={isFileSelected(selectedMethod)}
            onChange={() => onMethodChange('file')}
          />
          <label className="govuk-label govuk-radios__label" htmlFor="method-file">
            Upload data set to Bus Open Data Service
          </label>
        </div>
        {isFileSelected(selectedMethod) && (
          <div className="govuk-form-group">
            <label className="govuk-label" htmlFor="id_upload_file">
              Upload file
            </label>
            {fileHint && <div className="govuk-hint">{fileHint}</div>}
            {errors?.file && <p className="govuk-error-message">{errors.file}</p>}
            <input
              className="govuk-file-upload"
              id="id_upload_file"
              type="file"
              accept={fileAccept}
              onChange={(e) => onFileChange(e.target.files?.[0] || null)}
            />
          </div>
        )}
      </div>
    </>
  );
}
