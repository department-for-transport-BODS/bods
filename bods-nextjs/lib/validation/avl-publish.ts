import { AVL_PUBLISH_ERRORS } from './messages';

export interface AvlDescriptionInput {
  description: string;
  shortDescription: string;
}

export interface AvlUploadInput {
  urlLink: string;
  username: string;
  password: string;
}

export interface AvlCommentInput {
  comment: string;
}

export const validateAvlDescriptionStep = ({
  description,
  shortDescription,
}: AvlDescriptionInput): Record<string, string> => {
  const errors: Record<string, string> = {};

  if (!description.trim()) {
    errors.description = AVL_PUBLISH_ERRORS.description;
  }

  if (!shortDescription.trim()) {
    errors.shortDescription = AVL_PUBLISH_ERRORS.shortDescription;
  }

  return errors;
};

export const validateAvlUploadStep = ({
  urlLink,
  username,
  password,
}: AvlUploadInput): Record<string, string> => {
  const errors: Record<string, string> = {};

  if (!urlLink.trim()) {
    errors.urlLink = AVL_PUBLISH_ERRORS.urlLink;
  } else {
    try {
      const parsed = new URL(urlLink);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        errors.urlLink = AVL_PUBLISH_ERRORS.invalidUrlLink;
      }
    } catch {
      errors.urlLink = AVL_PUBLISH_ERRORS.invalidUrlLink;
    }
  }

  if (!username.trim()) {
    errors.username = AVL_PUBLISH_ERRORS.username;
  }

  if (!password.trim()) {
    errors.password = AVL_PUBLISH_ERRORS.password;
  }

  return errors;
};

export const validateAvlCommentStep = ({ comment }: AvlCommentInput): Record<string, string> => {
  if (comment.trim()) {
    return {};
  }

  return { comment: AVL_PUBLISH_ERRORS.comment };
};

export const validateAvlConsentStep = (consentChecked: boolean): Record<string, string> => {
  if (consentChecked) {
    return {};
  }

  return { consent: AVL_PUBLISH_ERRORS.consent };
};
