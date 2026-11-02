

export const LOGIN_ERRORS = {
  emailRequired: 'Please provide an email',
  emailInvalid: 'Enter an email address in the right format, like name@example.com',
  passwordRequired: 'Please provide a password',
  invalidCredentials: 'The email address and/or password you specified are not correct.',
  unverifiedEmail: (email: string) =>
    `The email address ${email} has not yet been verified. We have sent you another confirmation email.`,
  tooManyAttempts: 'Too many failed login attempts. Try again later.',
} as const;

export const TIMETABLE_PUBLISH_ERRORS = {
  dataSetDesc: 'Enter a description in the data set description box below',
  shortDesc: 'Enter a short description in the data set short description box below',
  method: 'Select how you want to provide your data set',
  link: 'Please provide a URL link',
  fileMissing: 'Please provide a file',
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
