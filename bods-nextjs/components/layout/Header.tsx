/**
 * Header Component
 * 
 * Uses GDS Header component from kainossoftwareltd-govuk-react-kainos
 * Must be a client component due to useAuth and GDS library browser globals
 */

'use client';

import { useAuth } from '@/hooks/useAuth';
import dynamic from 'next/dynamic';

const GDSHeader = dynamic(
  () => import('kainossoftwareltd-govuk-react-kainos').then((mod) => mod.Header),
  { ssr: false }
);

export function Header() {
  const { user } = useAuth();

  return (
    <GDSHeader
      serviceName="Bus Open Data Service"
      serviceUrl="/"
      user={user ? `${user.first_name} ${user.last_name}`.trim() || user.email : undefined}
      signOutUrl={user ? '/account/logout' : undefined}
      showNavigation={!!user}
    />
  );
}
