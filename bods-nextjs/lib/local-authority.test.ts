import { formatAuthIds, isValidAuthIds, licenceDetailUrl, truncateChars } from '@/lib/local-authority';

describe('local authority helpers', () => {
  it('formats auth ids like the Django list repr', () => {
    expect(formatAuthIds([1, 2])).toBe('[1, 2]');
    expect(formatAuthIds([7])).toBe('[7]');
  });

  it.each(['1', '1,2', '[1, 2]', '[1,2]', ' 3 , 4 '])('accepts auth_ids %p', (value) => {
    expect(isValidAuthIds(value)).toBe(true);
  });

  it.each([null, '', 'abc', '[1, a]', '1,', '[]', '1 2'])('rejects auth_ids %p', (value) => {
    expect(isValidAuthIds(value)).toBe(false);
  });

  it('truncates like Django truncatechars (length includes the ellipsis)', () => {
    expect(truncateChars('Short', 19)).toBe('Short');
    expect(truncateChars('Bournemouth Christchurch and Poole', 19)).toBe('Bournemouth Christ…');
    expect(truncateChars('Bournemouth Christ…', 19)).toHaveLength(19);
  });

  it('builds the licence link with org_id only when known', () => {
    expect(licenceDetailUrl('PD0000001', 12)).toMatch(/\/operators\/licence\/PD0000001\/\?org_id=12$/);
    expect(licenceDetailUrl('PD0000001', null)).toMatch(/\/operators\/licence\/PD0000001\/$/);
  });
});
