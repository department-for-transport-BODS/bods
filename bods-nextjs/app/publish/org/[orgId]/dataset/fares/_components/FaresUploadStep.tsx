'use client';

import { FormEvent } from 'react';
import { DataProviderRadioGroup, UPLOAD_FILE_ITEM_ID, URL_LINK_ITEM_ID } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';

export { UPLOAD_FILE_ITEM_ID, URL_LINK_ITEM_ID };

export type FaresUploadItem = typeof UPLOAD_FILE_ITEM_ID | typeof URL_LINK_ITEM_ID;

type FaresUploadStepProps = Readonly<{
  selectedItem: FaresUploadItem | null;
  urlLink: string;
  isSubmitting: boolean;
  errorMessage: string;
  heading: string;
  submitButtonText: string;
  errorTitleId: string;
  disableCancel?: boolean;
  onSelectedItemChange: (value: FaresUploadItem) => void;
  onUrlLinkChange: (value: string) => void;
  onUploadFileChange: (file: File | null) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}>;

/** Django `FaresFeedUploadForm`, shared by the fares publish, update and modify wizards. */
export function FaresUploadStep({
  selectedItem,
  urlLink,
  isSubmitting,
  errorMessage,
  heading,
  submitButtonText,
  errorTitleId,
  disableCancel = false,
  onSelectedItemChange,
  onUrlLinkChange,
  onUploadFileChange,
  onSubmit,
  onCancel,
}: FaresUploadStepProps) {
  return (
    <form onSubmit={onSubmit} noValidate>
      <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId={errorTitleId} />
      <DataProviderRadioGroup
        legend={heading}
        selectedMethod={selectedItem}
        link={urlLink}
        urlHint="Please provide a URL link where your NeTEX files are hosted. Example address: 'mybuscompany.com/fares.xml'."
        fileHint="This must be either NeTEX (see description in guidance) or a zip consisting only of NeTEX files"
        urlAriaLabel="url link"
        fileAriaLabel="Choose file"
        onMethodChange={(method) => onSelectedItemChange(method === 'link' ? URL_LINK_ITEM_ID : UPLOAD_FILE_ITEM_ID)}
        onLinkChange={onUrlLinkChange}
        onFileChange={onUploadFileChange}
      />
      <div className="govuk-button-group">
        <button className="govuk-button" type="submit" name="submit" value="submit" data-module="govuk-button" disabled={isSubmitting}>
          {submitButtonText}
        </button>
        <button
          className="govuk-button govuk-button--secondary"
          type="button"
          name="cancel"
          value="cancel"
          data-module="govuk-button"
          onClick={onCancel}
          disabled={disableCancel}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
