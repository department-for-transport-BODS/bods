import "server-only";
import { buildBodsHosts, getBodsBaseDomain } from './hosts';

const djangoInternalOrigin = process.env.DJANGO_INTERNAL_ORIGIN || 'http://localhost:8000';
const mapboxToken = process.env.MAPBOX_KEY || '';
const supportPhone = process.env.SUPPORT_PHONE || '0808 172 4134';
const supportEmail = process.env.SUPPORT_EMAIL || 'support@busopendataservice.atlassian.net';
const avlIpAllowList = process.env.AVL_IP_ADDRESS_LIST || '';

function djangoPublicPort(): string {
  if (getBodsBaseDomain() !== 'localhost') {
    return '';
  }

  try {
    return new URL(djangoInternalOrigin).port || '8000';
  } catch {
    return '8000';
  }
}

export const DJANGO_HOSTS = buildBodsHosts(getBodsBaseDomain(), djangoPublicPort());

// ECS runtime configuration for server imports only; pass browser-safe values to clients explicitly.
// Note : Whilst the Mapbox, and support details are displayed to the client they are not available at build time, and hence brought in as server values.
export const serverConfig = {
  djangoInternalOrigin,
  mapboxToken,
  supportPhone,
  supportEmail,
  avlIpAllowList,
} as const;