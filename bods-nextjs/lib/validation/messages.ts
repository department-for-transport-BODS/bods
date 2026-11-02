

// Django `FeedUploadForm`/`FaresFeedUploadForm` `url_link`/`upload_file` error messages. The
// no-selection error is raised by `clean()` on the `url_link` field.
export const DATA_SET_UPLOAD_ERRORS = {
  noSelection: 'Please provide a file or url',
  link: 'Please provide a URL link',
  fileMissing: 'Please provide a file',
} as const;

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
