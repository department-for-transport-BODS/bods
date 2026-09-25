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

const dataApiPageRoutes: Record<string, string> = {
  '/api': '/data/api/',
  '/api/timetable-openapi': '/data/timetable-openapi/',
  '/api/buslocation-api': '/data/buslocation-api/',
  '/api/buslocation-api/openapi': '/data/buslocation-api/openapi/',
  '/api/fares-openapi': '/data/fares-openapi/',
  '/api/disruptions-api-overview': '/data/disruptions-api-overview/',
  '/api/disruptions-openapi': '/data/disruptions-openapi/',
  '/api/cancellations-api-overview': '/data/cancellations-api-overview/',
  '/api/cancellations-openapi': '/data/cancellations-openapi/',
};

const djangoDataPagePrefixes = [
  '/api/buslocation-api/subscribe',
  '/api/buslocation-api/manage-subscriptions',
];

const wwwOnlyRoutePrefixes = [
  '/accessibility',
  '/changelog',
  '/contact',
  '/cookie',
  '/privacy-policy',
  '/version',
];

// Account pages exist on every service host (matching the Django service, where
// allauth is mounted per subdomain) so sign-in/out stay on the host the user
// came from and the session cookie is set for that host.
const sharedRoutePrefixes = [
  '/account/login',
  '/account/logout',
  '/account/logout-success',
  '/account/signup',
  '/account/account-exists',
  '/account/password',
  '/account/confirm-email',
  '/account/settings',
  '/account/agent',
  '/invitations/accept-invite',
];

function hasRoutePrefix(pathname: string, routePrefix: string): boolean {
  return pathname === routePrefix || pathname.startsWith(`${routePrefix}/`);
}

function isSharedAccountPath(pathname: string): boolean {
  if (pathname === '/account' || pathname === '/account/') {
    return true;
  }

  return sharedRoutePrefixes.some((prefix) => hasRoutePrefix(pathname, prefix));
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

  if (pathname.startsWith('/_next') || pathname.startsWith('/openapi/')) {
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

  const pathWithoutTrailingSlash = pathname.replace(/\/$/, '');
  const dataApiPageRoute = dataApiPageRoutes[pathWithoutTrailingSlash];
  if (subdomain === 'data' && dataApiPageRoute) {
    const url = request.nextUrl.clone();
    url.pathname = dataApiPageRoute;
    return NextResponse.rewrite(url);
  }

  if (
    subdomain === 'data' &&
    djangoDataPagePrefixes.some((prefix) => hasRoutePrefix(pathWithoutTrailingSlash, prefix))
  ) {
    const url = request.nextUrl.clone();
    url.pathname = `/api/data/${pathname.slice('/api/'.length)}`;
    return NextResponse.rewrite(url);
  }

  if (pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

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

  if (
    subdomain !== 'www' &&
    wwwOnlyRoutePrefixes.some((prefix) => hasRoutePrefix(pathname, prefix))
  ) {
    return redirectToSubdomain(request, hostname, 'www', pathname);
  }

  if (isSharedAccountPath(pathname)) {
    return NextResponse.next();
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
  matcher: ['/((?!_next/static|_next/image|favicon.ico|govuk|assets|public).*)'],
};
