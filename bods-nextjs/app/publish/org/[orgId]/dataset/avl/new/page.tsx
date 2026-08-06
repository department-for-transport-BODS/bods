import type { Metadata } from 'next';
import { connection } from 'next/server';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { serverConfig } from '@/config/server';
import { AVLCreatePageContent } from '../_components/AVLCreatePageContent';

export const metadata: Metadata = {
  title: 'Publish new data feed',
};

export default async function AVLCreatePage() {
  await connection();

  return (
    <ProtectedRoute>
      <AVLCreatePageContent avlIpAllowList={serverConfig.avlIpAllowList} />
    </ProtectedRoute>
  );
}
