export const BODS_SUBDOMAINS = ['www', 'data', 'publish', 'admin'] as const;

export type BodsSubdomain = (typeof BODS_SUBDOMAINS)[number];

export function getBodsBaseDomain(): string {
  return process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN || 'localhost';
}

export function hostnameWithoutPort(hostname: string): string {
  return hostname.trim().split(':')[0];
}

export function firstHeaderValue(value: string | null | undefined): string {
  return (value || '').split(',')[0].trim();
}

export function hostnameFromHeaders(
  hostHeader: string | null,
  forwardedHostHeader: string | null,
): string {
  return firstHeaderValue(hostHeader) || firstHeaderValue(forwardedHostHeader);
}

export function isBodsSubdomain(value: string): value is BodsSubdomain {
  return (BODS_SUBDOMAINS as readonly string[]).includes(value);
}

export function bodsAreaFromHostname(hostname: string): BodsSubdomain {
  const label = hostnameWithoutPort(hostname).split('.')[0];
  return isBodsSubdomain(label) ? label : 'www';
}

export function isAllowedBodsHostname(hostname: string, baseDomain: string): boolean {
  const host = hostnameWithoutPort(hostname).toLowerCase();
  if (!host) {
    return false;
  }

  if (baseDomain === 'localhost') {
    return host === 'localhost' || host.endsWith('.localhost');
  }

  if (host === baseDomain.toLowerCase()) {
    return true;
  }

  const suffix = `.${baseDomain.toLowerCase()}`;
  if (!host.endsWith(suffix)) {
    return false;
  }

  return isBodsSubdomain(host.slice(0, -suffix.length));
}

export function hostPath(origin: string, path = '/'): string {
  if (!path || path === '/') {
    return origin;
  }

  if (path.startsWith('?')) {
    return `${origin}${path}`;
  }

  return `${origin}${path.startsWith('/') ? path : `/${path}`}`;
}

export function buildBodsHosts(
  baseDomain: string,
  port: string,
): Record<BodsSubdomain, string> {
  const isLocalDomain = baseDomain === 'localhost';
  const scheme = isLocalDomain ? 'http' : 'https';
  const portSuffix = port ? `:${port}` : '';

  function hostname(subdomain: BodsSubdomain): string {
    if (!isLocalDomain) {
      return `${subdomain}.${baseDomain}`;
    }

    return subdomain === 'www' ? 'localhost' : `${subdomain}.localhost`;
  }

  return {
    www: `${scheme}://${hostname('www')}${portSuffix}`,
    data: `${scheme}://${hostname('data')}${portSuffix}`,
    publish: `${scheme}://${hostname('publish')}${portSuffix}`,
    admin: `${scheme}://${hostname('admin')}${portSuffix}`,
  };
}
