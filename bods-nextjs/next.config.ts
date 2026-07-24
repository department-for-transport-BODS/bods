import path from "node:path";
import type { NextConfig } from "next";

const djangoOrigin =
  process.env.DJANGO_INTERNAL_ORIGIN ||
  process.env.NEXT_PUBLIC_DJANGO_API_URL ||
  'http://localhost:8000';

const nextConfig: NextConfig = {
  output: 'standalone',

  // Transpile the GDS component library and govuk-frontend
  transpilePackages: ['govuk-frontend'],

  turbopack: {
    root: path.join(__dirname),
  },

  async rewrites() {
    return [
      // Download/report routes - must be handled by Next.js handlers, not proxied
      {
        source: '/api/avl/consumer-feedback/:path*',
        destination: '/api/avl/consumer-feedback/:path*',
      },
      {
        source: '/api/avl/consumer-interactions/:path*',
        destination: '/api/avl/consumer-interactions/:path*',
      },
      // Proxy everything else in /api/ to Django
      {
        source: '/api/:path*/',
        destination: `${djangoOrigin}/api/:path*/`,
      },
      {
        source: '/api/:path*',
        destination: `${djangoOrigin}/api/:path*`,
      },
      {
        source: '/admin/:path*',
        destination: '/admin/:path*',
      },
    ];
  },
  skipTrailingSlashRedirect: true,
  trailingSlash: false,
};

export default nextConfig;
