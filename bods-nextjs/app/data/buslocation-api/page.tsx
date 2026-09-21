import { ApiOverviewPage } from '@/components/data/api-overview/ApiOverviewPage';
import { API_OVERVIEWS } from '@/components/data/api-overview/config';

export const metadata = { title: 'Location data API Service - Bus Open Data Service' };

export default function LocationApiOverviewPage() {
  return <ApiOverviewPage config={API_OVERVIEWS.location} />;
}