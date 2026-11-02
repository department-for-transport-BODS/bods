import { EDIT_DESCRIPTION_ERRORS } from './messages';

export interface EditDescriptionInput {
  description: string;
  shortDescription: string;
}

export type EditDescriptionErrors = Partial<Record<keyof EditDescriptionInput, string>>;

export const validateEditDescription = ({
  description,
  shortDescription,
}: EditDescriptionInput): EditDescriptionErrors => {
  const errors: EditDescriptionErrors = {};

  if (!description.trim()) {
    errors.description = EDIT_DESCRIPTION_ERRORS.description;
  }
  if (!shortDescription.trim()) {
    errors.shortDescription = EDIT_DESCRIPTION_ERRORS.shortDescription;
  }

  return errors;
};
