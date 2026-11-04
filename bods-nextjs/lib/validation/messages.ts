

export const LOGIN_ERRORS = {
  emailRequired: 'Please provide an email',
  emailInvalid: 'Enter an email address in the right format, like name@example.com',
  passwordRequired: 'Please provide a password',
  invalidCredentials: 'The email address and/or password you specified are not correct.',
  unverifiedEmail: (email: string) =>
    `The email address ${email} has not yet been verified. We have sent you another confirmation email.`,
  tooManyAttempts: 'Too many failed login attempts. Try again later.',
}
// Django `FeedUploadForm`/`FaresFeedUploadForm` `url_link`/`upload_file` error messages. The
// no-selection error is raised by `clean()` on the `url_link` field.
export const DATA_SET_UPLOAD_ERRORS = {
  noSelection: 'Please provide a file or url',
  link: 'Please provide a URL link',
  fileMissing: 'Please provide a file',
} as const;

/** `transit_odp.publish.constants.REQUIRED_COMMENT_ERROR_MESSAGE`. */
export const REQUIRED_COMMENT_ERROR = 'Enter a comment in the box below';

export const TIMETABLE_PUBLISH_ERRORS = {
  dataSetDesc: 'Enter a description in the data set description box below',
  shortDesc: 'Enter a short description in the data set short description box below',
  method: DATA_SET_UPLOAD_ERRORS.noSelection,
  link: DATA_SET_UPLOAD_ERRORS.link,
  fileMissing: DATA_SET_UPLOAD_ERRORS.fileMissing,
  fileType:
    'The selected file must be a TransXChange XML file or a zip file containing only TransXChange files',
  consent: 'You must confirm you have reviewed the data quality report before publishing',
} as const;

export const AVL_PUBLISH_ERRORS = {
  description: 'Enter a description in the data feed description box below',
  shortDescription: 'Enter a short description in the data feed short description box below',
  urlLink: 'Please provide a URL link',
  invalidUrlLink: 'Enter a valid URL to your data feed',
  username: 'Please provide a username',
  password: 'Please provide a password',
  comment: 'Please provide a comment',
  consent: 'You must confirm you have reviewed the data quality report before publishing',
} as const;

// Django `FaresFeedDescriptionForm` / `FaresFeedUploadForm` (transit_odp/fares/forms.py).
// The no-selection error is raised by `clean()` on the `url_link` field. URL and file format
// errors ("Enter a valid URL to your data set", "The file is not in a correct format") come
// back from the create API's `field_errors`.
export const FARES_PUBLISH_ERRORS = {
  description: 'Enter a description in the data set description box below',
  shortDescription: 'Enter a short description in the data set short description box below',
  noSelection: 'Please provide a file or url',
  urlLink: 'Please provide a URL link',
  uploadFile: 'Please provide a file',
  emptyUploadFile: 'Please provide a non-empty file',
} as const;

// EditFeedDescriptionForm in transit_odp/publish/forms/dataset.py and transit_odp/fares/forms.py.
export const EDIT_DESCRIPTION_ERRORS = {
  description: 'Enter a description in the data set description box below',
  shortDescription: 'Enter a short description in the data set short description box below',
} as const;
