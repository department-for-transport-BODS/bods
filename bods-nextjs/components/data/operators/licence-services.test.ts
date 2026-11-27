import type { LicenceService } from '@/lib/operators';
import { initialFilters, mapRegistrationNumber, matchesFilters, sortServices } from './licence-services';

function service(overrides: Partial<LicenceService> = {}): LicenceService {
  return {
    serviceNumber: '1',
    registrationNumber: 'PD0000001:1',
    fullRegistrationNumber: '1 - PD0000001:1',
    licenceOrganisationId: 10,
    localAuthorityIds: '5',
    isInScope: true,
    isInSeason: true,
    requiresAttention: false,
    avlRequiresAttention: false,
    faresRequiresAttention: false,
    isLabelGreen: true,
    labelStr: 'Compliant',
    ...overrides,
  };
}

describe('initialFilters', () => {
  it('ticks every LTA, franchise and operator plus in scope and in season', () => {
    expect(initialFilters([1, 2], true, [3], [4])).toEqual({
      ltas: ['1', '2', 'blank'],
      inScope: true,
      outOfScope: false,
      inSeason: true,
      outOfSeason: false,
      franchises: [3],
      operators: [4],
    });
  });
});

describe('matchesFilters', () => {
  const filters = initialFilters([5], true, [], [10]);

  it('shows in scope, in season services for a ticked LTA and operator', () => {
    expect(matchesFilters(service(), filters)).toBe(true);
  });

  it('hides out of scope and out of season services until their boxes are ticked', () => {
    expect(matchesFilters(service({ isInScope: false }), filters)).toBe(false);
    expect(matchesFilters(service({ isInSeason: false }), filters)).toBe(false);
    expect(matchesFilters(service({ isInScope: false }), { ...filters, outOfScope: true })).toBe(true);
    expect(matchesFilters(service({ isInSeason: false }), { ...filters, outOfSeason: true })).toBe(true);
  });

  it('treats a scope group with nothing ticked as everything', () => {
    const none = { ...filters, inScope: false, outOfScope: false };
    expect(matchesFilters(service({ isInScope: false }), none)).toBe(true);
  });

  it('matches services without an LTA through the Not Assigned box', () => {
    const blank = service({ localAuthorityIds: '' });
    expect(matchesFilters(blank, filters)).toBe(true);
    expect(matchesFilters(blank, { ...filters, ltas: ['5'] })).toBe(false);
  });

  it('matches a service when any of its LTAs is ticked', () => {
    expect(matchesFilters(service({ localAuthorityIds: '8,5' }), { ...filters, ltas: ['5'] })).toBe(true);
    expect(matchesFilters(service({ localAuthorityIds: '8,9' }), { ...filters, ltas: ['5'] })).toBe(false);
  });

  it('filters by operator or franchise organisation', () => {
    expect(matchesFilters(service({ licenceOrganisationId: 11 }), filters)).toBe(false);
    expect(matchesFilters(service({ licenceOrganisationId: 11 }), { ...filters, franchises: [11] })).toBe(true);
    expect(matchesFilters(service({ licenceOrganisationId: null }), filters)).toBe(false);
  });
});

describe('mapRegistrationNumber', () => {
  it('is "<service number> - <registration number>"', () => {
    expect(mapRegistrationNumber(service())).toBe('1 - PD0000001:1');
  });
});

describe('sortServices', () => {
  const services = [
    service({ fullRegistrationNumber: '10 - B', requiresAttention: true }),
    service({ fullRegistrationNumber: '2 - A', avlRequiresAttention: true }),
    service({ fullRegistrationNumber: 'abc', faresRequiresAttention: true }),
  ];

  it('sorts by the registration text, ascending or descending', () => {
    expect(sortServices(services, 0, true).map((s) => s.fullRegistrationNumber)).toEqual(['10 - B', '2 - A', 'abc']);
    expect(sortServices(services, 0, false).map((s) => s.fullRegistrationNumber)).toEqual(['abc', '2 - A', '10 - B']);
  });

  it('sorts the attention columns with requiring-attention services last when ascending', () => {
    expect(sortServices(services, 1, true)[2].fullRegistrationNumber).toBe('10 - B');
    expect(sortServices(services, 2, false)[0].fullRegistrationNumber).toBe('2 - A');
    expect(sortServices(services, 3, false)[0].fullRegistrationNumber).toBe('abc');
  });

  it('does not mutate the input', () => {
    const copy = [...services];
    sortServices(services, 0, false);
    expect(services).toEqual(copy);
  });
});
