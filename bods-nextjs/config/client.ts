import { version } from '../package.json';

const bodsBaseDomain = process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN || 'localhost';
const isLocalDomain = bodsBaseDomain === 'localhost';

function hostOrigin(subdomain: string): string {
  const hostname = isLocalDomain
    ? subdomain === 'www'
      ? 'localhost'
      : `${subdomain}.localhost`
    : `${subdomain}.${bodsBaseDomain}`;
  const scheme = isLocalDomain ? 'http' : 'https';
  const port = isLocalDomain ? ':8000' : '';

  return `${scheme}://${hostname}${port}`;
}

export const HOSTS = {
  www: hostOrigin('www'),
  data: hostOrigin('data'),
  publish: hostOrigin('publish'),
  admin: hostOrigin('admin'),
} as const;

// Build-time, client-safe configuration; do not add runtime-only or secret values.
export const clientConfig = {
  // App
  appVersion: version,
  bodsBaseUrl: bodsBaseDomain,
  nodeEnv: process.env.NODE_ENV || 'development',
} as const;