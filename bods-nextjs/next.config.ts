import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',

  // Transpile the GDS component library and govuk-frontend
  transpilePackages: ['govuk-frontend'],

  turbopack: {
    root: path.join(__dirname),
  },

  skipTrailingSlashRedirect: true,
  trailingSlash: false,
};

export default nextConfig;
