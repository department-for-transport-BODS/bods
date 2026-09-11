import { ApiDocumentationPage } from '@/components/data/api-documentation/ApiDocumentationPage';
import { API_DOCUMENTATION } from '@/components/data/api-documentation/config';

export const metadata = { title: 'Location data API - Bus Open Data Service' };

export default function LocationApiDocumentationPage() {
  return <ApiDocumentationPage config={API_DOCUMENTATION.location} />;
}