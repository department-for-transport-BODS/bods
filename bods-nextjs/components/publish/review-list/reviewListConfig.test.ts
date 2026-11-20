import { djangoTitle } from './reviewListConfig';

describe('djangoTitle', () => {
  it.each([
    ['Review my timetables data', 'Review My Timetables Data'],
    ['Review my bus location data', 'Review My Bus Location Data'],
    ["Review O'NEIL coaches fares data", "Review O'Neil Coaches Fares Data"],
    ["Review bob's buses fares data", "Review Bob's Buses Fares Data"],
    ['Review 1st Bus timetables data', 'Review 1st Bus Timetables Data'],
  ])('matches Django title() for %s', (input, expected) => {
    expect(djangoTitle(input)).toBe(expected);
  });
});
