import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import {
  bodsAreaFromHostname,
  getBodsBaseDomain,
  hostnameFromHeaders,
  hostnameWithoutPort,
  isAllowedBodsHostname,
} from './config/hosts';

const subdomainRoutes: Record<string, string> = {
  www: '/',
  data: '/data',
  publish: '/publish',
  admin: '/admin',
};

const wwwOnlyRoutePrefixes = [
  '/accessibility',
  '/changelog',
  '/contact',
  '/cookie',
  '/privacy-policy',
  '/version',
  '/account/login',
  '/account/logout',
  '/account/signup',
  '/account/password',
  '/account/confirm-email',
];

function hasRoutePrefix(pathname: string, routePrefix: string): boolean {
  return pathname === routePrefix || pathname.startsWith(`${routePrefix}/`);
}

function publicPath(pathname: string, routePrefix: string): string | null {
  if (routePrefix === '/') {
    return null;
  }

  if (pathname === routePrefix) {
    return '/';
  }

  if (hasRoutePrefix(pathname, routePrefix)) {
    return pathname.slice(routePrefix.length);
  }

  return null;
}

function hostForSubdomain(hostname: string, subdomain: string): string {
  const host = hostnameWithoutPort(hostname);

  if (host === 'localhost') {
    return subdomain === 'www' ? host : `${subdomain}.${host}`;
  }

  const hostParts = host.split('.');
  if (subdomainRoutes[hostParts[0]]) {
    hostParts[0] = subdomain;
    return hostParts.join('.');
  }

  return `${subdomain}.${host}`;
}

function redirectToSubdomain(
  request: NextRequest,
  hostname: string,
  subdomain: string,
  pathname: string,
): NextResponse {
  const url = request.nextUrl.clone();
  url.hostname = hostForSubdomain(hostname, subdomain);
  url.pathname = pathname;
  return NextResponse.redirect(url);
}

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  if (pathname.startsWith('/api/') || pathname.startsWith('/_next')) {
    return NextResponse.next();
  }

  const hostname = hostnameFromHeaders(
    request.headers.get('host'),
    request.headers.get('x-forwarded-host'),
  );
  const baseDomain = getBodsBaseDomain();

  if (!isAllowedBodsHostname(hostname, baseDomain)) {
    return NextResponse.next();
  }

  const subdomain = bodsAreaFromHostname(hostname);
  const routePrefix = subdomainRoutes[subdomain];

  for (const [ownedSubdomain, ownedPrefix] of Object.entries(subdomainRoutes)) {
    if (ownedPrefix !== '/' && hasRoutePrefix(pathname, ownedPrefix) && ownedSubdomain !== subdomain) {
      return redirectToSubdomain(
        request,
        hostname,
        ownedSubdomain,
        pathname.slice(ownedPrefix.length) || '/',
      );
    }
  }

  if (pathname === '/account' && subdomain !== 'publish' && subdomain !== 'www') {
    return redirectToSubdomain(request, hostname, 'publish', '/account');
  }

  if (
    subdomain !== 'www' &&
    wwwOnlyRoutePrefixes.some((prefix) => hasRoutePrefix(pathname, prefix))
  ) {
    return redirectToSubdomain(request, hostname, 'www', pathname);
  }

  const canonicalPath = publicPath(pathname, routePrefix);

  if (canonicalPath) {
    const url = request.nextUrl.clone();
    url.pathname = canonicalPath;
    return NextResponse.redirect(url);
  }

  if (routePrefix === '/') {
    return NextResponse.next();
  }

  if (!hasRoutePrefix(pathname, routePrefix)) {
    const url = request.nextUrl.clone();
    url.pathname = `${routePrefix}${pathname === '/' ? '' : pathname}`;
    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|govuk|public).*)'],
};
