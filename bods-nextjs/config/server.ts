import "server-only"
const djangoInternalOrigin = process.env.DJANGO_INTERNAL_ORIGIN || 'http://localhost:8000';
const mapboxToken = process.env.MAPBOX_KEY || '';
const supportPhone = process.env.SUPPORT_PHONE || '0808 172 4134';
const supportEmail = process.env.SUPPORT_EMAIL || 'support@busopendataservice.atlassian.net';
const avlIpAllowList = process.env.AVL_IP_ADDRESS_LIST || '';

// ECS runtime configuration for server imports only; pass browser-safe values to clients explicitly.
// Note : Whilst the Mapbox, and support details are displayed to the client they are not available at build time, and hence brought in as server values.
export const serverConfig = {
  djangoInternalOrigin,
  mapboxToken,
  supportPhone,
  supportEmail,
  avlIpAllowList,
} as const;