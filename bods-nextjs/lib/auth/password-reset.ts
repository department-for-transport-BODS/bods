/**
 * Carries the email a password reset was requested for, and parses the
 * uidb36-key segment allauth puts in the reset URL.
 */

const STORAGE_KEY = 'bods:password-reset-email';
const UIDB36_RE = /^[0-9A-Za-z]+$/;

export function rememberPasswordResetEmail(email: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.sessionStorage.setItem(STORAGE_KEY, email);
  } catch {
    // Storage can be unavailable; the done page falls back to "you".
  }
}

export function readPasswordResetEmail(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function subscribeToPasswordResetEmail(): () => void {
  return () => {};
}

export function passwordResetEmailServerSnapshot(): null {
  return null;
}

/**
 * allauth's reset URL is /account/password/reset/key/<uidb36>-<key>/.
 * uidb36 is alphanumeric; the key may contain further hyphens.
 */
export function parsePasswordResetUidKey(
  uidKey: string,
): { uidb36: string; key: string } | null {
  const separator = uidKey.indexOf('-');
  if (separator < 1 || separator === uidKey.length - 1) {
    return null;
  }

  const uidb36 = uidKey.slice(0, separator);
  if (!UIDB36_RE.test(uidb36)) {
    return null;
  }

  return { uidb36, key: uidKey.slice(separator + 1) };
}

/** Full page load so AuthProvider picks up the session the reset API just set. */
export function goToPasswordResetSuccess(): void {
  window.location.assign('/account/password/reset/key/done');
}
