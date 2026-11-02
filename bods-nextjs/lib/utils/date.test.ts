import { formatDateWithOrdinal } from './date';

describe('formatDateWithOrdinal', () => {
  it.each([
    ['2021-08-02', '2nd August 2021'],
    ['2021-08-01', '1st August 2021'],
    ['2021-08-03T10:00:00Z', '3rd August 2021'],
    ['2021-08-04', '4th August 2021'],
    ['2021-08-11', '11th August 2021'],
    ['2021-08-12', '12th August 2021'],
    ['2021-08-13', '13th August 2021'],
    ['2021-08-21', '21st August 2021'],
    ['2021-08-22', '22nd August 2021'],
    ['2021-12-31', '31st December 2021'],
  ])('formats %s as %s', (input, expected) => {
    expect(formatDateWithOrdinal(input)).toBe(expected);
  });

  it.each([undefined, null, '', 'not a date'])('returns a dash for %p', (input) => {
    expect(formatDateWithOrdinal(input)).toBe('-');
  });
});
