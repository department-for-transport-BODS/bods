
const STORAGE_KEY = 'bods:invite-email';

export function rememberInviteEmail(email: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.sessionStorage.setItem(STORAGE_KEY, email);
  } catch {
    // Storage can be unavailable; the success page omits the address.
  }
}

export function readInviteEmail(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function subscribeToInviteEmail(): () => void {
  return () => {};
}

export function inviteEmailServerSnapshot(): null {
  return null;
}
