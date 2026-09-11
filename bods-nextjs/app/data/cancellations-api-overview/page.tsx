import { ApiOverviewPage } from '@/components/data/api-overview/ApiOverviewPage';
import { API_OVERVIEWS } from '@/components/data/api-overview/config';

export const metadata = { title: 'Cancellations data API - Bus Open Data Service' };

export default function CancellationsApiOverviewPage() {
  return <ApiOverviewPage config={API_OVERVIEWS.cancellations} />;
}