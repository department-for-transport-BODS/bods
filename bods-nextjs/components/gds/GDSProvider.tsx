'use client';

import { ReactNode, useEffect } from 'react';

interface GDSProviderProps {
  children: ReactNode;
}

export function GDSProvider({ children }: GDSProviderProps) {
  useEffect(() => {
    import('govuk-frontend').then(({ initAll }) => initAll());
  }, []);

  return <>{children}</>;
}

