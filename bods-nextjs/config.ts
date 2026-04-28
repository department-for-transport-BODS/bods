import { version } from './package.json';

export const config = {
  // API URLs — must be set in every environment
  djangoApiUrl: process.env.NEXT_PUBLIC_DJANGO_API_URL!,
  djangoOrigin: process.env.DJANGO_INTERNAL_ORIGIN || 'http://localhost:8000',
  djangoApiBaseUrl: process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000',

  // Mapbox
  mapboxToken: process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '',

  // Support
  supportPhone: process.env.NEXT_PUBLIC_SUPPORT_PHONE || '0808 172 4134',
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@busopendataservice.atlassian.net',

  // App
  appVersion: version,
  bodsBaseUrl: process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN || 'bus-data.dft.gov.uk',
  nodeEnv: process.env.NODE_ENV || 'development',
} as const;

export const HOSTS = {
  root: `https://www.${config.bodsBaseUrl}`,
  data: `https://data.${config.bodsBaseUrl}`,
  publish: `https://publish.${config.bodsBaseUrl}`,
  admin: `https://admin.${config.bodsBaseUrl}`,
} as const;