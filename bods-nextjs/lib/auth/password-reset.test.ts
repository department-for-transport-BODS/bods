/** @jest-environment node */

import { parsePasswordResetUidKey } from './password-reset';

describe('parsePasswordResetUidKey', () => {
  it('splits uidb36 from a hyphenated allauth key', () => {
    expect(parsePasswordResetUidKey('MQ-abc-def-ghi')).toEqual({
      uidb36: 'MQ',
      key: 'abc-def-ghi',
    });
  });

  it('rejects a segment with no hyphen or empty parts', () => {
    expect(parsePasswordResetUidKey('MQ')).toBeNull();
    expect(parsePasswordResetUidKey('-abc')).toBeNull();
    expect(parsePasswordResetUidKey('MQ-')).toBeNull();
  });

  it('rejects a uidb36 that is not alphanumeric', () => {
    expect(parsePasswordResetUidKey('M_Q-abc')).toBeNull();
  });
});
