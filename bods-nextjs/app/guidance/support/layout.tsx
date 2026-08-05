import { connection } from 'next/server';
import type { ReactNode } from 'react';
import { serverConfig } from '@/config/server';
import { SupportConfigProvider } from './SupportConfigProvider';

export default async function SupportLayout({ children }: { children: ReactNode }) {
  await connection();

  return (
    <SupportConfigProvider supportEmail={serverConfig.supportEmail}>
      {children}
    </SupportConfigProvider>
  );
}