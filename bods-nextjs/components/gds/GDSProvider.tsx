'use client';

import { initAll } from 'govuk-frontend';
import { ReactNode, useEffect } from 'react';

interface GDSProviderProps {
  children: ReactNode;
}

export function GDSProvider({ children }: GDSProviderProps) {
  useEffect(() => {
    initAll();
  }, []);

  return <>{children}</>;
}

