import type { Metadata } from 'next';
import { connection } from 'next/server';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { config } from '@/runtime-config';
import { AVLUpdatePageContent } from '../_components/AVLUpdatePageContent';

export const metadata: Metadata = {
  title: 'Update data feed',
};

export default async function AVLUpdatePage() {
  await connection();

  return (
    <ProtectedRoute>
      <AVLUpdatePageContent avlIpAllowList={config.avlIpAllowList} />
    </ProtectedRoute>
  );
}
