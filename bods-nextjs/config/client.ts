import { version } from '../package.json';
import { buildBodsHosts, getBodsBaseDomain, hostPath } from './hosts';

const bodsBaseDomain = getBodsBaseDomain();
const isLocalDomain = bodsBaseDomain === 'localhost';
const bodsPort = process.env.NEXT_PUBLIC_BODS_PORT || (isLocalDomain ? '3000' : '');

export const HOSTS = buildBodsHosts(bodsBaseDomain, bodsPort);

export { hostPath };

export function wwwPath(path = '/'): string {
  return hostPath(HOSTS.www, path);
}

export function dataPath(path = '/'): string {
  return hostPath(HOSTS.data, path);
}

export function publishPath(path = '/'): string {
  return hostPath(HOSTS.publish, path);
}

function stripAppPrefix(path: string, prefix: string): string {
  if (path === prefix) {
    return '/';
  }

  if (path.startsWith(`${prefix}/`)) {
    return path.slice(prefix.length);
  }

  return path;
}

export function publishAppPath(path: string): string {
  return publishPath(stripAppPrefix(path, '/publish'));
}

// Build-time, client-safe configuration; do not add runtime-only or secret values.
export const clientConfig = {
  // App
  appVersion: version,
  bodsBaseUrl: bodsBaseDomain,
  nodeEnv: process.env.NODE_ENV || 'development',
} as const;
