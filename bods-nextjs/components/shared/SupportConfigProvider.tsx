'use client';

import { createContext, useContext, type ReactNode } from 'react';

type SupportConfig = {
  supportEmail: string;
};

const SupportConfigContext = createContext<SupportConfig | null>(null);

export function SupportConfigProvider({
  children,
  supportEmail,
}: SupportConfig & { children: ReactNode }) {
  return (
    <SupportConfigContext value={{ supportEmail }}>
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