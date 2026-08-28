import { HOSTS } from '@/config/client';

function hostFromOrigin(origin: string): string | null {
  try {
    return new URL(origin).host;
  } catch {
    return null;
  }
}

const allowedHosts = new Set(
  [HOSTS.www, HOSTS.data, HOSTS.publish, HOSTS.admin]
    .map((origin) => hostFromOrigin(origin))
    .filter((host): host is string => Boolean(host)),
);

/**
 * Resolve a post-login destination from ?next=.
 * Only same-site BODS hosts are accepted; otherwise fall back to www home.
 */
export function resolvePostLoginRedirect(next: string | null | undefined): string {
  if (!next) {
    return HOSTS.www;
  }

  // Relative path on the current (www) host – keep local.
  if (next.startsWith('/') && !next.startsWith('//')) {
    return next;
  }

  try {
    const url = new URL(next);
    if ((url.protocol === 'http:' || url.protocol === 'https:') && allowedHosts.has(url.host)) {
      return url.toString();
    }
  } catch {
    // ignore invalid URLs
  }

  return HOSTS.www;
}

/**
 * Build a login URL carrying a next= return address. A relative loginBaseUrl is
 * resolved against returnTo, keeping sign-in on the host the user came from
 * (allauth is mounted per subdomain in Django).
 */
export function loginUrlWithNext(loginBaseUrl: string, returnTo: string): string {
  const url = new URL(loginBaseUrl, returnTo);
  url.searchParams.set('next', returnTo);
  return url.toString();
}
