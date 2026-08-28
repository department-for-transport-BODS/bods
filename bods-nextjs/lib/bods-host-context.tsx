'use client';

import { createContext, useContext, type ReactNode } from 'react';
import { bodsAreaFromHostname, type BodsSubdomain } from '@/config/hosts';

const BodsAreaContext = createContext<BodsSubdomain | undefined>(undefined);

export function HostProvider({
  hostname,
  children,
}: {
  hostname: string;
  children: ReactNode;
}) {
  return (
    <BodsAreaContext.Provider value={bodsAreaFromHostname(hostname)}>
      {children}
    </BodsAreaContext.Provider>
  );
}

export function useBodsArea(): BodsSubdomain {
  const area = useContext(BodsAreaContext);
  if (area === undefined) {
    throw new Error('useBodsArea must be used within HostProvider');
  }
  return area;
}
