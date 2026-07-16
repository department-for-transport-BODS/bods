import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const subdomainRoutes: Record<string, string> = {
  www: '/',
  data: '/data',
  publish: '/publish',
  admin: '/admin',
};

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

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
  matcher: ['/((?!_next/static|_next/image|favicon.ico|govuk|public).*)'],
};
