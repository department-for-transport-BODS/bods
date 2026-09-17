'use client';

import { createContext, useContext, type ReactNode } from 'react';

type SupportConfig = {
  supportEmail: string;
  ptiPdfUrl: string;
};

const SupportConfigContext = createContext<SupportConfig | null>(null);

export function SupportConfigProvider({
  children,
  supportEmail,
  ptiPdfUrl,
}: SupportConfig & { children: ReactNode }) {
  return (
    <SupportConfigContext value={{ supportEmail, ptiPdfUrl }}>
      {children}
    </SupportConfigContext>
  );
}

export function useSupportConfig(): SupportConfig {
  const config = useContext(SupportConfigContext);

  if (!config) {
    throw new Error('useSupportConfig must be used within SupportConfigProvider');
  }

  return config;
}
