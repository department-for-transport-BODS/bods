import { connection } from 'next/server';
import type { ReactNode } from 'react';
import { config } from '@/runtime-config';
import { SupportConfigProvider } from './SupportConfigProvider';

export default async function SupportLayout({ children }: { children: ReactNode }) {
  await connection();

  return (
    <SupportConfigProvider supportEmail={config.supportEmail}>
      {children}
    </SupportConfigProvider>
  );
}