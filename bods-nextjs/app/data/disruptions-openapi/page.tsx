import { connection } from 'next/server';
import { ApiDocumentationPage } from '@/components/data/api-documentation/ApiDocumentationPage';
import { API_DOCUMENTATION } from '@/components/data/api-documentation/config';
import { featureFlags } from '@/config/feature-flags';

export const metadata = { title: 'Disruptions data API - Bus Open Data Service' };

export default async function DisruptionsApiDocumentationPage() {
  await connection();

  const config = featureFlags.isGtfsServiceAlertsLive
    ? { ...API_DOCUMENTATION.disruptions, schemaFile: 'disruptions-with-gtfs-service-alerts.yml' }
    : API_DOCUMENTATION.disruptions;

  return <ApiDocumentationPage config={config} />;
}
