import { ApiOverviewPage } from '@/components/data/api-overview/ApiOverviewPage';
import { API_OVERVIEWS } from '@/components/data/api-overview/config';

export const metadata = { title: 'Disruptions data API - Bus Open Data Service' };

export default function DisruptionsApiOverviewPage() {
  return <ApiOverviewPage config={API_OVERVIEWS.disruptions} />;
}