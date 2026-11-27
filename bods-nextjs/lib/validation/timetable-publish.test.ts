import {
  validateTimetableStep1,
  validateTimetableStep2,
  validateTimetableStep3,
} from './timetable-publish';
import { TIMETABLE_PUBLISH_ERRORS } from './messages';

describe('validateTimetableStep1', () => {
  it.each([
    {
      name: 'returns no errors when both descriptions are provided',
      input: { dataSetDesc: 'A description', shortDesc: 'Short' },
      expected: {},
    },
    {
      name: 'flags whitespace-only descriptions as missing',
      input: { dataSetDesc: '   ', shortDesc: '   ' },
      expected: {
        dataSetDesc: TIMETABLE_PUBLISH_ERRORS.dataSetDesc,
        shortDesc: TIMETABLE_PUBLISH_ERRORS.shortDesc,
      },
    },
    {
      name: 'flags only the missing description field',
      input: { dataSetDesc: 'A description', shortDesc: '' },
      expected: { shortDesc: TIMETABLE_PUBLISH_ERRORS.shortDesc },
    },
  ])('$name', ({ input, expected }) => {
    expect(validateTimetableStep1(input)).toEqual(expected);
  });
});

describe('validateTimetableStep2', () => {
  it.each([
    {
      name: 'requires a method to be selected',
      input: { selectedMethod: '' as const, link: '', file: null },
      expected: { method: TIMETABLE_PUBLISH_ERRORS.method },
    },
    {
      name: 'requires a non-empty link when the link method is selected',
      input: { selectedMethod: 'link' as const, link: '   ', file: null },
      expected: { link: TIMETABLE_PUBLISH_ERRORS.link },
    },
    {
      name: 'accepts a valid link',
      input: {
        selectedMethod: 'link' as const,
        link: 'https://example.com/timetable.xml',
        file: null,
      },
      expected: {},
    },
    {
      name: 'requires a file when the file method is selected',
      input: { selectedMethod: 'file' as const, link: '', file: null },
      expected: { file: TIMETABLE_PUBLISH_ERRORS.fileMissing },
    },
  ])('$name', ({ input, expected }) => {
    expect(validateTimetableStep2(input)).toEqual(expected);
  });

  it.each(['timetable.txt', 'timetable.csv', 'timetable'])(
    'rejects non-TransXChange file %s',
    (fileName) => {
      const file = new File(['data'], fileName, { type: 'text/plain' });

      expect(validateTimetableStep2({ selectedMethod: 'file', link: '', file })).toEqual({
        file: TIMETABLE_PUBLISH_ERRORS.fileType,
      });
    },
  );

  it.each(['timetable.xml', 'timetable.XML', 'timetable.zip', 'timetable.ZIP'])(
    'accepts TransXChange file %s regardless of case',
    (fileName) => {
      const file = new File(['data'], fileName, { type: 'application/octet-stream' });

      expect(validateTimetableStep2({ selectedMethod: 'file', link: '', file })).toEqual({});
    },
  );
});

describe('validateTimetableStep3', () => {
  it.each([
    { consentChecked: true, expected: {} },
    { consentChecked: false, expected: { consent: TIMETABLE_PUBLISH_ERRORS.consent } },
  ])(
    'returns the expected result when consentChecked is $consentChecked',
    ({ consentChecked, expected }) => {
      expect(validateTimetableStep3(consentChecked)).toEqual(expected);
    },
  );
});
