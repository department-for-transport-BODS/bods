export interface ApiOverviewConfig {
  title: string;
  openApiHref: string;
  tryApiLabel: string;
  description?: string;
  subscriptionLinks?: readonly {
    label: string;
    href: string;
  }[];
}

export const API_OVERVIEWS = {
  location: {
    title: 'Location data API Service',
    openApiHref: '/api/buslocation-api/openapi/',
    tryApiLabel: 'Try API',
    subscriptionLinks: [
      {
        label: 'Create Location Data Subscription',
        href: '/api/buslocation-api/subscribe/',
      },
      {
        label: 'Manage subscriptions',
        href: '/api/buslocation-api/manage-subscriptions/',
      },
    ],
  },
  disruptions: {
    title: 'Disruptions data API',
    openApiHref: '/api/disruptions-openapi/',
    tryApiLabel: 'Try the disruptions data API',
    description:
      'Disruptions data is available in SIRI-SX or GTFS-RT. Disruptions data is created by local authorities and represents the disruption of vehicle networks.',
  },
  cancellations: {
    title: 'Cancellations data API',
    openApiHref: '/api/cancellations-openapi/',
    tryApiLabel: 'Try the cancellations data API',
    description:
      'Cancellations data is available in SIRI-SX. Cancellations data is created by operators and represents specific vehicle journey cancellations.',
  },
} as const satisfies Record<string, ApiOverviewConfig>;