import { connection } from 'next/server';
import { featureFlags } from '@/config/feature-flags';
import { serverConfig } from '@/config/server';
import { DownloadsContent } from './_components/DownloadsContent';

export const metadata = {
  title: 'Download all data - Bus Open Data Service',
  description: 'Download all data published on the Bus Open Data Service.',
};

export default async function DownloadsPage() {
  // Flags and the PTI profile URL are runtime (ECS) values, so never prerender them at build time.
  await connection();

  return (
    <DownloadsContent
      isGtfsServiceAlertsLive={featureFlags.isGtfsServiceAlertsLive}
      ptiPdfUrl={serverConfig.ptiPdfUrl}
    />
  );
}
