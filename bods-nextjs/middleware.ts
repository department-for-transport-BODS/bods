/**
 * Next.js Middleware
 *
 * Handles subdomain routing for the application
 * This will need looking at at the end of the ticket - fine for local now
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const subdomainRoutes: Record<string, string> = {
  www: '/',
  data: '/data',
  publish: '/publish',
  admin: '/admin',
};

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const subdomain = hostname.split('.')[0];

  if (subdomain && subdomainRoutes[subdomain]) {
    const pathname = request.nextUrl.pathname;

    if (!pathname.startsWith(subdomainRoutes[subdomain])) {
      const newPath = `${subdomainRoutes[subdomain]}${pathname === '/' ? '' : pathname}`;
      return NextResponse.rewrite(new URL(newPath, request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     * - govuk assets
     */
    '/((?!_next/static|_next/image|favicon.ico|govuk|public).*)',
  ],
};
