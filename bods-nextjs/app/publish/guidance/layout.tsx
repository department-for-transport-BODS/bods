import { connection } from 'next/server';
import type { ReactNode } from 'react';
import { serverConfig } from '@/config/server';
import { SupportConfigProvider } from '@/components/shared/SupportConfigProvider';

export default async function PublishGuidanceLayout({ children }: { children: ReactNode }) {
  await connection();

  return (
    <SupportConfigProvider supportEmail={serverConfig.supportEmail}>
      {children}
    </SupportConfigProvider>
  );
}
