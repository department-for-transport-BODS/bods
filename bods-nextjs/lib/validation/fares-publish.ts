import { FARES_PUBLISH_ERRORS } from './messages';

export const FARES_URL_LINK_ITEM_ID = 'url_link-conditional';
export const FARES_UPLOAD_FILE_ITEM_ID = 'upload_file-conditional';

export type FaresUploadItem = typeof FARES_URL_LINK_ITEM_ID | typeof FARES_UPLOAD_FILE_ITEM_ID;

export interface FaresDescriptionInput {
  description: string;
  shortDescription: string;
}

export interface FaresUploadInput {
  selectedItem: FaresUploadItem | null;
  urlLink: string;
  uploadFile: File | null;
}

export type FaresUploadErrors = { urlLink?: string; uploadFile?: string };

export const validateFaresDescriptionStep = ({
  description,
  shortDescription,
}: FaresDescriptionInput): { description?: string; shortDescription?: string } => {
  const errors: { description?: string; shortDescription?: string } = {};

  if (!description.trim()) {
    errors.description = FARES_PUBLISH_ERRORS.description;
  }

  if (!shortDescription.trim()) {
    errors.shortDescription = FARES_PUBLISH_ERRORS.shortDescription;
  }

  return errors;
};

// Mirrors `FaresFeedUploadForm.clean()`; URL format and file contents are left to Django.
export const validateFaresUploadStep = ({
  selectedItem,
  urlLink,
  uploadFile,
}: FaresUploadInput): FaresUploadErrors => {
  if (selectedItem === FARES_UPLOAD_FILE_ITEM_ID) {
    if (!uploadFile) {
      return { uploadFile: FARES_PUBLISH_ERRORS.uploadFile };
    }
    if (uploadFile.size === 0) {
      return { uploadFile: FARES_PUBLISH_ERRORS.emptyUploadFile };
    }
    return {};
  }

  if (selectedItem === FARES_URL_LINK_ITEM_ID) {
    return urlLink.trim() ? {} : { urlLink: FARES_PUBLISH_ERRORS.urlLink };
  }

  return { urlLink: FARES_PUBLISH_ERRORS.noSelection };
};
