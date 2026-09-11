import { ApiDocumentationPage } from '@/components/data/api-documentation/ApiDocumentationPage';
import { API_DOCUMENTATION } from '@/components/data/api-documentation/config';

export const metadata = { title: 'Cancellations data API - Bus Open Data Service' };

export default function CancellationsApiDocumentationPage() {
  return <ApiDocumentationPage config={API_DOCUMENTATION.cancellations} />;
}