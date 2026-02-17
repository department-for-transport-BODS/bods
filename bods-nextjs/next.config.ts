import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Transpile the GDS component library and govuk-frontend
  transpilePackages: ['kainossoftwareltd-govuk-react-kainos', 'govuk-frontend'],

  // This will need to be looked at again when we move to close the ticket off.
  async rewrites() {
    return [
      {
        source: '/admin/:path*',
        destination: '/admin/:path*',
      },
    ];
  },
  trailingSlash: false,
};

export default nextConfig;
