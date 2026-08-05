import type { Metadata } from 'next';
import { connection } from 'next/server';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { serverConfig } from '@/config/server';
import { AVLUpdatePageContent } from '../_components/AVLUpdatePageContent';

export const metadata: Metadata = {
  title: 'Update data feed',
};

export default async function AVLUpdatePage() {
  await connection();

  return (
    <ProtectedRoute>
      <AVLUpdatePageContent avlIpAllowList={serverConfig.avlIpAllowList} />
    </ProtectedRoute>
  );
}
