import { ApiDocumentationPage } from '@/components/data/api-documentation/ApiDocumentationPage';
import { API_DOCUMENTATION } from '@/components/data/api-documentation/config';

export const metadata = { title: 'Fares data API - Bus Open Data Service' };

export default function FaresApiDocumentationPage() {
  return <ApiDocumentationPage config={API_DOCUMENTATION.fares} />;
}