import { headers } from 'next/headers';
import { notFound } from 'next/navigation';
import { bodsAreaFromHostname, hostnameFromHeaders } from '@/config/hosts';
import UserRedirectPage from './UserRedirectPageContent';

export default async function Page() {
  const requestHeaders = await headers();
  const hostname = hostnameFromHeaders(requestHeaders.get('host'), requestHeaders.get('x-forwarded-host'));

  // Django mounts account/~redirect/ on the data, publish and admin hosts only;
  // www only has the allauth account routes, so it is a 404 there.
  if (bodsAreaFromHostname(hostname) === 'www') {
    notFound();
  }

  return <UserRedirectPage />;
}
