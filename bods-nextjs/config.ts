export const config = {
  // API URLs
  djangoApiUrl: process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000',
  // Mapbox
  mapboxToken: process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '',

  // Support
  supportPhone: process.env.NEXT_PUBLIC_SUPPORT_PHONE || '0808 172 4134',
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@busopendataservice.atlassian.net',

  // App
  appVersion: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  nodeEnv: process.env.NODE_ENV || 'development',
  cookieDomain: process.env.NEXT_PUBLIC_COOKIE_DOMAIN || '',
} as const;
