import { ApiDocumentationPage } from '@/components/data/api-documentation/ApiDocumentationPage';
import { API_DOCUMENTATION } from '@/components/data/api-documentation/config';

export const metadata = { title: 'Use Bus Open Data Service API' };

export default function TimetablesApiDocumentationPage() {
  return <ApiDocumentationPage config={API_DOCUMENTATION.timetables} />;
}