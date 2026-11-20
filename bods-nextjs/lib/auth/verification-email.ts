/**
 * Carries the email address a verification link was sent to from the signup page
 * to the "verify your email" page, mirroring the session stash Django uses.
 */

const STORAGE_KEY = 'bods:verification-email';

export function rememberVerificationEmail(email: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.sessionStorage.setItem(STORAGE_KEY, email);
  } catch {
    // Storage can be unavailable (private mode, disabled cookies); the page
    // falls back to a message without the address.
  }
}

export function readVerificationEmail(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

/**
 * The stash only changes between page loads, so there is nothing to subscribe
 * to; this exists to read it through useSyncExternalStore, which keeps the
 * server render and hydration consistent.
 */
export function subscribeToVerificationEmail(): () => void {
  return () => {};
}

export function verificationEmailServerSnapshot(): null {
  return null;
}
