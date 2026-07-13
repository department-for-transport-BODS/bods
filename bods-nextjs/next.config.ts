import type { NextConfig } from "next";

const djangoOrigin =
  process.env.DJANGO_INTERNAL_ORIGIN ||
  process.env.NEXT_PUBLIC_DJANGO_API_URL ||
  'http://localhost:8000';

const nextConfig: NextConfig = {
  // Transpile the GDS component library and govuk-frontend
  transpilePackages: ['kainossoftwareltd-govuk-react-kainos', 'govuk-frontend'],

  async rewrites() {
    return [
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
  trailingSlash: false,
};

export default nextConfig;
