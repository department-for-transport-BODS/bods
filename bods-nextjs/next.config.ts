import path from "node:path";
import type { NextConfig } from "next";

const djangoOrigin =
  process.env.DJANGO_INTERNAL_ORIGIN ||
  process.env.NEXT_PUBLIC_DJANGO_API_URL ||
  'http://localhost:8000';

const nextConfig: NextConfig = {
  // Transpile the GDS component library and govuk-frontend
  transpilePackages: ['govuk-frontend'],

  turbopack: {
    root: path.join(__dirname),
  },

  async rewrites() {
    return [
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
