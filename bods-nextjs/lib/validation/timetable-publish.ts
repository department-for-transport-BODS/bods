/**
 * Validation helpers for the timetable publish flow.
 *
 * Each validator is a pure function that takes the relevant form state and
 * returns a `Record<string, string>` of field -> error message. An empty
 * object means the step is valid. Pages call these, then call `setErrors`
 * with the result.
 *
 * Centralising validation (and the error copy in `./messages`) keeps the
 * page components focused on rendering and state, and makes the rules easy
 * to reuse / unit test.
 */

import { TIMETABLE_PUBLISH_ERRORS } from './messages';

export type TimetablePublishMethod = 'link' | 'file' | '';

export interface TimetableStep1Input {
  dataSetDesc: string;
  shortDesc: string;
}

export interface TimetableStep2Input {
  selectedMethod: TimetablePublishMethod;
  link: string;
  file: File | null;
}

const isTransXChangeFile = (file: File): boolean => {
  const name = file.name.toLowerCase();
  return name.endsWith('.xml') || name.endsWith('.zip');
};

export const validateTimetableStep1 = ({
  dataSetDesc,
  shortDesc,
}: TimetableStep1Input): Record<string, string> => {
  const errors: Record<string, string> = {};

  if (!dataSetDesc.trim()) {
    errors.dataSetDesc = TIMETABLE_PUBLISH_ERRORS.dataSetDesc;
  }
  if (!shortDesc.trim()) {
    errors.shortDesc = TIMETABLE_PUBLISH_ERRORS.shortDesc;
  }

  return errors;
};

export const validateTimetableStep2 = ({
  selectedMethod,
  link,
  file,
}: TimetableStep2Input): Record<string, string> => {
  const errors: Record<string, string> = {};

  if (!selectedMethod) {
    errors.method = TIMETABLE_PUBLISH_ERRORS.method;
  } else if (selectedMethod === 'link' && !link.trim()) {
    errors.link = TIMETABLE_PUBLISH_ERRORS.link;
  } else if (selectedMethod === 'file') {
    if (!file) {
      errors.file = TIMETABLE_PUBLISH_ERRORS.fileMissing;
    } else if (!isTransXChangeFile(file)) {
      errors.file = TIMETABLE_PUBLISH_ERRORS.fileType;
    }
  }

  return errors;
};

export const validateTimetableStep3 = (consentChecked: boolean): Record<string, string> => {
  if (consentChecked) {
    return {};
  }
  return { consent: TIMETABLE_PUBLISH_ERRORS.consent };
};
