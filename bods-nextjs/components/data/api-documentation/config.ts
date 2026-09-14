export interface ApiDocumentationConfig {
  title: string;
  schemaFile: string;
  schemaLabel: string;
  overview?: {
    title: string;
    href: string;
  };
}

export const API_DOCUMENTATION = {
  timetables: {
    title: 'Timetables data API',
    schemaFile: 'timetables.yml',
    schemaLabel: 'timetables',
  },
  location: {
    title: 'Location data API',
    schemaFile: 'avl-with-subscriptions.yml',
    schemaLabel: 'location',
    overview: {
      title: 'Location data API Service',
      href: '/api/buslocation-api/',
    },
  },
  fares: {
    title: 'Fares data API',
    schemaFile: 'fares.yml',
    schemaLabel: 'fares',
  },
  disruptions: {
    title: 'Disruptions data API',
    schemaFile: 'disruptions-with-gtfs-service-alerts.yml',
    schemaLabel: 'disruptions',
    overview: {
      title: 'Disruptions data API',
      href: '/api/disruptions-api-overview/',
    },
  },
  cancellations: {
    title: 'Cancellations data API',
    schemaFile: 'cancellations.yml',
    schemaLabel: 'cancellations',
    overview: {
      title: 'Cancellations data API',
      href: '/api/cancellations-api-overview/',
    },
  },
} as const satisfies Record<string, ApiDocumentationConfig>;